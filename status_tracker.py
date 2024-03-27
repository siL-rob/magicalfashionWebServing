import redis
import time

r = redis.Redis(host='10.0.3.6', port=6379, db=1)

# def check_task_status(sketch_id):
#     for _ in range(90):  # 최대 대기 시간(초)
#         status = r.get(f'sketchtoreal:{sketch_id}:status')
#         if status and status.decode('utf-8') == 'completed':
#             return True
#         time.sleep(1)
#     return False

# def get_task_result(sketch_id):
#     result_data = r.get(f'sketchtoreal:{sketch_id}:image')
#     if result_data:
#         return result_data
#     return None

def check_task_status(task_id, timeout=60):
    """Celery 작업의 완료 상태를 확인합니다."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        status = r.get(f'task:{task_id}:status')
        if status and status.decode('utf-8') == 'completed':
            return True
        time.sleep(1)
    return False

# def get_task_result(task_id):
#     """완료된 작업의 결과를 가져옵니다."""
#     result_data = r.get(f'task:{task_id}:result')
#     if result_data:
#         return result_data
#     return None

def get_task_result(task_id, result_type):
    """완료된 작업의 결과를 가져옵니다."""
    result_data = r.get(f'task:{task_id}:{result_type}')
    if result_data:
        return result_data
    return None