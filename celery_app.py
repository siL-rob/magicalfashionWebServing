from celery import Celery


celery_app = Celery('app', broker='redis://10.0.3.6:6379/0', backend='redis://10.0.3.6:6379/1')

celery_app.conf.task_routes = {
    'inference_controlnet_tasks.sketch_to_real': {'queue': 'controlnet_q'},
    'real_to_wrap' : { 'queue':'wrap_q'},
    'test.wearing_cloth' : {'queue':'dci_q'}
}