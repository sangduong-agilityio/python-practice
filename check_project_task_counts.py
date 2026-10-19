import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect the distribution of tasks per project_id in tms_db
# Or we can write a simple SQL script to see which project has few tasks
sql = """
SELECT project_id, COUNT(*) as task_count 
FROM tasks 
GROUP BY project_id 
ORDER BY task_count ASC;
"""
print("SQL to check task count per project:")
print(sql)
