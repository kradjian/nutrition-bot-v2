"""Database layer with Repository pattern"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class NutritionEntry:
    """Domain model for nutrition entry"""
    id: Optional[int]
    user_id: int
    date: str
    timestamp: str
    raw_input: str
    items: List[Dict[str, Any]]
    total_calories: float
    total_protein: float
    total_fat: float
    total_carbs: float


@dataclass 
class DailySummary:
    """Summary statistics for a day"""
    calories: float
    protein: float
    fat: float
    carbs: float
    entries_count: int


@dataclass
class CustomFood:
    """Custom food template with fixed nutrition values"""
    id: Optional[int]
    user_id: int
    name: str
    aliases: str  # comma-separated alternative names
    grams: int
    calories: float
    protein: float
    fat: float
    carbs: float
    created_at: Optional[str] = None


class NutritionRepository:
    """Repository for nutrition data access"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    raw_input TEXT NOT NULL,
                    items_json TEXT NOT NULL DEFAULT '[]',
                    total_calories REAL DEFAULT 0,
                    total_protein REAL DEFAULT 0,
                    total_fat REAL DEFAULT 0,
                    total_carbs REAL DEFAULT 0
                )
            """)
            
            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_date ON entries(user_id, date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON entries(timestamp)")
            
            # Custom foods table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_foods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    aliases TEXT DEFAULT '',
                    grams INTEGER DEFAULT 100,
                    calories REAL DEFAULT 0,
                    protein REAL DEFAULT 0,
                    fat REAL DEFAULT 0,
                    carbs REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_custom_foods_user ON custom_foods(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_custom_foods_name ON custom_foods(name)")
            
            # User settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'ru',
                    timezone TEXT DEFAULT 'UTC',
                    day_end_hour INTEGER DEFAULT 4,
                    goal_calories INTEGER DEFAULT 2000,
                    goal_protein REAL DEFAULT 100,
                    goal_fat REAL DEFAULT 70,
                    goal_carbs REAL DEFAULT 250,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        logger.info("Database initialized")
    
    def save_entry(
        self,
        user_id: int,
        raw_input: str,
        items: List[Dict[str, Any]],
        totals: Dict[str, float]
    ) -> int:
        """Save nutrition entry and return its ID"""
        now = datetime.now()
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO entries 
                (user_id, date, timestamp, raw_input, items_json, 
                 total_calories, total_protein, total_fat, total_carbs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    now.strftime("%Y-%m-%d"),
                    now.isoformat(),
                    raw_input,
                    json.dumps(items, ensure_ascii=False),
                    totals.get("calories", 0),
                    totals.get("protein", 0),
                    totals.get("fat", 0),
                    totals.get("carbs", 0)
                )
            )
            entry_id = cursor.lastrowid
        
        logger.info(f"Saved entry {entry_id} for user {user_id}")
        return entry_id
    
    def get_daily_summary(self, user_id: int, date_str: str, timezone: str = 'UTC', day_end_hour: int = 4) -> DailySummary:
        """Get summary for specific date with timezone support"""
        from timezone_utils import get_day_start_end
        
        # Get UTC boundaries for the logical day
        start_utc, end_utc = get_day_start_end(date_str, timezone, day_end_hour)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT 
                    COALESCE(SUM(total_calories), 0) as calories,
                    COALESCE(SUM(total_protein), 0) as protein,
                    COALESCE(SUM(total_fat), 0) as fat,
                    COALESCE(SUM(total_carbs), 0) as carbs,
                    COUNT(*) as entries
                FROM entries 
                WHERE user_id = ? 
                AND datetime(timestamp) >= datetime(?)
                AND datetime(timestamp) < datetime(?)
                """,
                (user_id, start_utc.isoformat(), end_utc.isoformat())
            )
            row = cursor.fetchone()
        
        return DailySummary(
            calories=round(row[0], 1),
            protein=round(row[1], 1),
            fat=round(row[2], 1),
            carbs=round(row[3], 1),
            entries_count=row[4]
        )
    
    def get_day_entries(self, user_id: int, date_str: str) -> List[NutritionEntry]:
        """Get all entries for a specific date"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, user_id, date, timestamp, raw_input, 
                       items_json, total_calories, total_protein, total_fat, total_carbs
                FROM entries 
                WHERE user_id = ? AND date = ?
                ORDER BY timestamp DESC
                """,
                (user_id, date_str)
            )
            rows = cursor.fetchall()
        
        entries = []
        for row in rows:
            entries.append(NutritionEntry(
                id=row[0],
                user_id=row[1],
                date=row[2],
                timestamp=row[3],
                raw_input=row[4],
                items=json.loads(row[5]),
                total_calories=row[6],
                total_protein=row[7],
                total_fat=row[8],
                total_carbs=row[9]
            ))
        
        return entries
    
    def delete_last_entry(self, user_id: int) -> bool:
        """Delete the most recent entry for user"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id FROM entries 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
                """,
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                conn.execute("DELETE FROM entries WHERE id = ?", (row[0],))
                logger.info(f"Deleted entry {row[0]} for user {user_id}")
                return True
        
        return False
    
    # Custom foods methods
    
    def save_custom_food(
        self,
        user_id: int,
        name: str,
        aliases: str,
        grams: int,
        calories: float,
        protein: float,
        fat: float,
        carbs: float
    ) -> int:
        """Save custom food template"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO custom_foods 
                (user_id, name, aliases, grams, calories, protein, fat, carbs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name.lower(), aliases.lower(), grams, calories, protein, fat, carbs)
            )
            food_id = cursor.lastrowid
        
        logger.info(f"Saved custom food '{name}' (id={food_id}) for user {user_id}")
        return food_id
    
    def get_custom_foods(self, user_id: int) -> List[CustomFood]:
        """Get all custom foods for user"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, user_id, name, aliases, grams, calories, protein, fat, carbs, created_at
                FROM custom_foods 
                WHERE user_id = ?
                ORDER BY name
                """,
                (user_id,)
            )
            rows = cursor.fetchall()
        
        return [
            CustomFood(
                id=row[0], user_id=row[1], name=row[2], aliases=row[3],
                grams=row[4], calories=row[5], protein=row[6], fat=row[7], carbs=row[8], created_at=row[9]
            )
            for row in rows
        ]
    
    def find_custom_food(self, user_id: int, query: str) -> Optional[CustomFood]:
        """Find custom food by name or alias (case-insensitive)"""
        query_lower = query.lower()
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, user_id, name, aliases, grams, calories, protein, fat, carbs, created_at
                FROM custom_foods 
                WHERE user_id = ? AND (
                    name LIKE ? OR aliases LIKE ?
                )
                LIMIT 1
                """,
                (user_id, f"%{query_lower}%", f"%{query_lower}%")
            )
            row = cursor.fetchone()
        
        if row:
            return CustomFood(
                id=row[0], user_id=row[1], name=row[2], aliases=row[3],
                grams=row[4], calories=row[5], protein=row[6], fat=row[7], carbs=row[8], created_at=row[9]
            )
        return None
    
    def delete_custom_food(self, user_id: int, food_id: int) -> bool:
        """Delete custom food by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM custom_foods WHERE id = ? AND user_id = ?",
                (food_id, user_id)
            )
            return cursor.rowcount > 0

    def update_custom_food(
        self,
        user_id: int,
        food_id: int,
        name: Optional[str] = None,
        aliases: Optional[str] = None,
        grams: Optional[int] = None,
        calories: Optional[float] = None,
        protein: Optional[float] = None,
        fat: Optional[float] = None,
        carbs: Optional[float] = None
    ) -> bool:
        """Update custom food fields by ID"""
        # Build update fields dynamically
        fields = []
        values = []

        if name is not None:
            fields.append("name = ?")
            values.append(name.lower())
        if aliases is not None:
            fields.append("aliases = ?")
            values.append(aliases.lower())
        if grams is not None:
            fields.append("grams = ?")
            values.append(grams)
        if calories is not None:
            fields.append("calories = ?")
            values.append(calories)
        if protein is not None:
            fields.append("protein = ?")
            values.append(protein)
        if fat is not None:
            fields.append("fat = ?")
            values.append(fat)
        if carbs is not None:
            fields.append("carbs = ?")
            values.append(carbs)

        if not fields:
            return False

        values.extend([food_id, user_id])

        with self._get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE custom_foods SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
                values
            )
            return cursor.rowcount > 0

    # User settings methods

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings, create default if not exists"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT language, timezone, day_end_hour,
                       goal_calories, goal_protein, goal_fat, goal_carbs
                FROM user_settings WHERE user_id = ?
                """,
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "language": row[0],
                    "timezone": row[1],
                    "day_end_hour": row[2],
                    "goal_calories": row[3],
                    "goal_protein": row[4],
                    "goal_fat": row[5],
                    "goal_carbs": row[6]
                }
            
            # Create default settings
            conn.execute(
                """
                INSERT INTO user_settings (user_id) VALUES (?)
                """,
                (user_id,)
            )
            
            return {
                "language": "ru",
                "timezone": "UTC",
                "day_end_hour": 4,
                "goal_calories": 2000,
                "goal_protein": 100,
                "goal_fat": 70,
                "goal_carbs": 250
            }

    def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """Update user settings"""
        allowed_fields = ['language', 'timezone', 'day_end_hour', 
                         'goal_calories', 'goal_protein', 'goal_fat', 'goal_carbs']
        
        fields = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                fields.append(f"{field} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        values.append(user_id)
        
        with self._get_connection() as conn:
            # Ensure record exists
            cursor = conn.execute(
                "SELECT 1 FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            if not cursor.fetchone():
                conn.execute(
                    "INSERT INTO user_settings (user_id) VALUES (?)",
                    (user_id,)
                )
            
            # Update
            cursor = conn.execute(
                f"""
                UPDATE user_settings 
                SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = ?
                """,
                values
            )
            return cursor.rowcount > 0
