#!/usr/bin/env python3
"""
Oceanus Agent Debug Tool.

A CLI utility to insert test Flink exceptions and check diagnosis status.
Useful for development, testing, and demos.

Usage:
    python scripts/debug_tool.py insert --type checkpoint
    python scripts/debug_tool.py insert --msg "Custom error message"
    python scripts/debug_tool.py status --job-id test-job-123
    python scripts/debug_tool.py list --limit 5
"""

import asyncio
import argparse
import uuid
import sys
import json
from datetime import datetime
from sqlalchemy import text
from oceanus_agent.config.settings import settings
from oceanus_agent.services.mysql_service import MySQLService

# Predefined error templates
ERROR_TEMPLATES = {
    "checkpoint": {
        "msg": "Checkpoint expired before completing. If you see this error consistently, consider increasing the checkpoint interval or timeout.",
        "type": "checkpoint_failure",
        "name": "Checkpoint Job"
    },
    "timeout": {
        "msg": "java.util.concurrent.TimeoutException: Heartbeat of TaskManager with id container_123 timed out.",
        "type": "task_manager_timeout",
        "name": "Timeout Job"
    },
    "oom_meta": {
        "msg": "java.lang.OutOfMemoryError: Metaspace. The Metaspace memory pool is full.",
        "type": "oom_metaspace",
        "name": "Metaspace OOM Job"
    },
    "oom_heap": {
        "msg": "java.lang.OutOfMemoryError: Java heap space. Dumping heap to /tmp/heapdump.hprof",
        "type": "oom_heap",
        "name": "Heap OOM Job"
    },
    "network": {
        "msg": "org.apache.flink.runtime.io.network.partition.PartitionNotFoundException: Partition xx not found.",
        "type": "network_partition_error",
        "name": "Network Job"
    }
}

async def insert_record(args):
    """Insert a test record into the database."""
    job_id = args.job_id or f"test-job-{uuid.uuid4().hex[:8]}"
    
    if args.msg:
        error_msg = args.msg
        error_type = args.error_type or "unknown"
        job_name = "Custom Debug Job"
    else:
        template = ERROR_TEMPLATES.get(args.type, ERROR_TEMPLATES["checkpoint"])
        error_msg = template["msg"]
        error_type = template["type"]
        job_name = template["name"]

    print(f"Inserting job: {job_id}")
    print(f"Error Type: {error_type}")
    print(f"Message: {error_msg[:100]}...")

    mysql_service = MySQLService(settings.mysql)
    
    query = text("""
    INSERT INTO flink_job_exceptions 
    (job_id, job_name, job_type, error_message, error_type, status)
    VALUES
    (:job_id, :job_name, 'streaming', :error_message, :error_type, 'pending');
    """)
    
    params = {
        "job_id": job_id,
        "job_name": job_name,
        "error_message": error_msg,
        "error_type": error_type
    }
    
    try:
        async with mysql_service.engine.begin() as conn:
            await conn.execute(query, params)
        print(f"\n✅ Successfully inserted test record. Job ID: {job_id}")
    except Exception as e:
        print(f"\n❌ Error inserting record: {e}")

async def check_status(args):
    """Check the status of a specific job."""
    if not args.job_id:
        print("❌ Error: --job-id is required for status command")
        return

    mysql_service = MySQLService(settings.mysql)
    
    query = text("""
    SELECT job_id, status, diagnosis_confidence, suggested_fix, created_at, updated_at
    FROM flink_job_exceptions 
    WHERE job_id = :job_id
    """)
    
    try:
        async with mysql_service.engine.connect() as conn:
            result = await conn.execute(query, {"job_id": args.job_id})
            row = result.fetchone()
            
            if row:
                print(f"\n📋 Job Details: {row[0]}")
                print(f"Status:     {row[1]}")
                print(f"Confidence: {row[2]}")
                print(f"Created:    {row[4]}")
                print(f"Updated:    {row[5]}")
                
                if row[3]:
                    print("\n💡 Suggested Fix:")
                    try:
                        fix_json = json.loads(row[3])
                        print(json.dumps(fix_json, indent=2, ensure_ascii=False))
                    except:
                        print(row[3])
            else:
                print(f"\n❌ No record found for Job ID: {args.job_id}")
    except Exception as e:
        print(f"\n❌ Error checking status: {e}")

async def list_records(args):
    """List recent records."""
    mysql_service = MySQLService(settings.mysql)
    
    limit = args.limit or 10
    
    query = text(f"""
    SELECT job_id, error_type, status, created_at
    FROM flink_job_exceptions 
    ORDER BY created_at DESC
    LIMIT :limit
    """)
    
    try:
        async with mysql_service.engine.connect() as conn:
            result = await conn.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            print(f"\nRecent {len(rows)} records:")
            print(f"{ 'Job ID':<25} {'Status':<12} {'Type':<20} {'Created At'}")
            print("-" * 80)
            
            for row in rows:
                print(f"{row[0]:<25} {row[1]:<12} {row[2][:20]:<20} {row[3]}")
                
    except Exception as e:
        print(f"\n❌ Error listing records: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Oceanus Agent Debug Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Insert Command
    insert_parser = subparsers.add_parser("insert", help="Insert a test record")
    insert_parser.add_argument("--type", choices=ERROR_TEMPLATES.keys(), default="checkpoint", help="Type of error template")
    insert_parser.add_argument("--msg", help="Custom error message")
    insert_parser.add_argument("--error-type", help="Custom error type label")
    insert_parser.add_argument("--job-id", help="Custom Job ID (optional)")

    # Status Command
    status_parser = subparsers.add_parser("status", help="Check diagnosis status")
    status_parser.add_argument("--job-id", required=True, help="Job ID to check")

    # List Command
    list_parser = subparsers.add_parser("list", help="List recent records")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of records to show")

    args = parser.parse_args()

    if args.command == "insert":
        await insert_record(args)
    elif args.command == "status":
        await check_status(args)
    elif args.command == "list":
        await list_records(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    # Ensure src is in python path
    import sys
    import os
    sys.path.append(os.path.join(os.getcwd(), "src"))
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
