from fastapi import APIRouter
from typing import Dict, List, Optional
from database import get_db
from models import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    db = get_db()
    cursor = db.cursor()
    
    # 1. Counts by status
    cursor.execute("SELECT status, COUNT(*) as count FROM applications GROUP BY status")
    status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
    
    total_applied = status_counts.get("applied", 0)
    total_screening = status_counts.get("screening", 0)
    total_interview = status_counts.get("interview", 0)
    total_offer = status_counts.get("offer", 0)
    total_rejected = status_counts.get("rejected", 0)
    total_archived = status_counts.get("archived", 0)
    
    total_apps = sum(status_counts.values())
    total_active = total_apps - total_archived - total_rejected
    
    # 2. Response Rate
    # (status != 'applied' and != 'archived') / total * 100
    responded_apps = total_apps - total_applied - total_archived
    response_rate = (responded_apps / total_apps * 100) if total_apps > 0 else 0.0
    
    # 3. Avg Days to Response
    # Average days between date_applied and last_activity for apps moved past 'applied'
    # SQLite julianday helps calculate differences between ISO dates
    cursor.execute("""
        SELECT AVG(julianday(last_activity) - julianday(date_applied)) as avg_days
        FROM applications 
        WHERE status NOT IN ('applied', 'archived') 
        AND date_applied IS NOT NULL 
        AND last_activity IS NOT NULL
    """)
    avg_days_row = cursor.fetchone()
    avg_days_to_response = avg_days_row["avg_days"] if avg_days_row and avg_days_row["avg_days"] is not None else None
    
    # 4. Pending Review
    cursor.execute("SELECT COUNT(*) FROM review_queue WHERE status = 'pending'")
    pending_review = cursor.fetchone()[0]
    
    # 5. Weekly Trend (Last 8 weeks)
    cursor.execute("""
        WITH RECURSIVE weeks(week_str) AS (
            SELECT strftime('%Y-W%W', date('now', '-7 days', 'weekday 0', '-7 weeks'))
            UNION ALL
            SELECT strftime('%Y-W%W', date(
                substr(week_str, 1, 4) || '-01-01', 
                '+' || (CAST(substr(week_str, 7, 2) AS INTEGER)) || ' weeks', 
                'weekday 0'
            ))
            FROM weeks
            LIMIT 8
        ),
        WeeklyApplied AS (
            SELECT strftime('%Y-W%W', created_at) as week, COUNT(*) as count
            FROM applications
            WHERE created_at >= date('now', '-8 weeks')
            GROUP BY week
        ),
        WeeklyResponses AS (
            SELECT strftime('%Y-W%W', last_activity) as week, COUNT(*) as count
            FROM applications
            WHERE status NOT IN ('applied', 'archived')
            AND last_activity >= date('now', '-8 weeks')
            GROUP BY week
        )
        SELECT 
            strftime('%Y-W%W', date('now', 'weekday 0', '-' || (n*7) || ' days')) as week,
            COALESCE((SELECT count FROM WeeklyApplied WHERE week = strftime('%Y-W%W', date('now', 'weekday 0', '-' || (n*7) || ' days'))), 0) as applied,
            COALESCE((SELECT count FROM WeeklyResponses WHERE week = strftime('%Y-W%W', date('now', 'weekday 0', '-' || (n*7) || ' days'))), 0) as responses
        FROM (SELECT 0 n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7)
        ORDER BY week ASC
    """)
    # Simplified approach for trend due to SQLite recursive complexity
    cursor.execute("""
        SELECT 
            strftime('%Y-W%W', created_at) as week,
            COUNT(*) as applied,
            SUM(CASE WHEN status NOT IN ('applied', 'archived') THEN 1 ELSE 0 END) as responses
        FROM applications
        WHERE created_at >= date('now', '-60 days')
        GROUP BY week
        ORDER BY week DESC
        LIMIT 8
    """)
    weekly_trend = [{"week": row["week"], "applied": row["applied"], "responses": row["responses"]} for row in cursor.fetchall()]
    weekly_trend.reverse() # Oldest first

    db.close()
    
    return DashboardStats(
        total_active=total_active,
        total_applied=total_applied,
        total_screening=total_screening,
        total_interview=total_interview,
        total_offer=total_offer,
        total_rejected=total_rejected,
        total_archived=total_archived,
        response_rate=round(response_rate, 1),
        avg_days_to_response=round(avg_days_to_response, 1) if avg_days_to_response is not None else None,
        pending_review=pending_review,
        weekly_trend=weekly_trend
    )

@router.get("/applications-by-status")
async def get_applications_by_status():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT status, COUNT(*) as count FROM applications GROUP BY status")
    rows = cursor.fetchall()
    db.close()
    
    counts = {
        "applied": 0,
        "screening": 0,
        "interview": 0,
        "offer": 0,
        "rejected": 0,
        "archived": 0
    }
    
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] = row["count"]
            
    return counts
