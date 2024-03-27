import streamlit as st
from PIL import Image
import io
import redis
import uuid
from celery import Celery

from celery_app import celery_app
from status_tracker import check_task_status, get_task_result


celery_app = Celery('app', broker='redis://10.0.3.6:6379/0', backend='redis://10.0.3.6:6379/1')

r = redis.Redis(host='10.0.3.6', port=6379, db=1)

# sketch_id=  str(uuid.uuid4()) # 고유 스케치 id 생성
sketch_id=  12 # 고유 스케치 id 생성

# 페이지 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 'upload_sketch'

# 스케치 업로드 페이지
if st.session_state.page == 'upload_sketch':
    st.title("의상 스케치 및 설명 업로드")
    
    sketch_image_file = st.file_uploader("스케치된 의상 이미지를 업로드하세요.", type=['jpg', 'jpeg', 'png'])
    prompt = st.text_input("스케치에 대한 설명을 입력하세요. (예: high quality garment photo of [black  long sleeve t-shirt] with white background ([]안 수정))")
    
    
    if sketch_image_file is not None and prompt:
        #이미지를 PIL 이미지로 변환
        image = Image.open(sketch_image_file)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr,format=image.format)
        img_byte_arr=img_byte_arr.getvalue()
        
        #이미지와 텍스트를 redis에 저장
        
        r.set(f'task:{sketch_id}:image', img_byte_arr)
        r.set(f'task:{sketch_id}:prompt', prompt)
        
        # 메시지 큐에 sketch_id 전송
        r.publish('sketch_channel', sketch_id)
        
        st.image(sketch_image_file, caption='업로드된 스케치', use_column_width=True)
        
        if st.button('스케치를 실제 의상으로 변환'):
            
            # Celery 작업 비동기적으로 실행
            task_send = celery_app.send_task('inference_controlnet_tasks.sketch_to_real', args=[sketch_id], queue='controlnet_q')
            st.write("변환 요청을 처리 중입니다. 잠시 후 결과를 확인하세요.")
            
            #task 상태에 따라 처리하는 로직(실제이미지의상보여줌)
            if check_task_status(sketch_id):
                real_dress_data = get_task_result(sketch_id, 'result')
                if real_dress_data:
                    real_dress_image = Image.open(io.BytesIO(real_dress_data))
                    st.image(real_dress_image, caption='변환된 실제 의상', use_column_width=True)
                    st.session_state.page = 'ask_for_tryon'
                else:
                    st.error("변환된 이미지를 불러올 수 없습니다.")
            else:
                st.error("작업이 시간 내에 완료되지 않았습니다. 나중에 다시 시도해주세요.")
            
            
         
# 착용샷 여부 질문 페이지
if st.session_state.page == 'ask_for_tryon':
    if st.button('실제 착용샷을 보시겠습니까?'):
        
        # r.publish('create_wear_shot', sketch_id)
        # 착용샷 생성 작업 요청175.45.205.214
        sketc_id=  13
        task_send = celery_app.send_task('eval_PBAFN_viton.real_to_wrap', args=[sketch_id, sketc_id], queue='wrap_q')
        # st.session_state.task_id_for_wear_shot = task_send.id  # 작업 ID 저장
        
        st.write("착용샷 생성 요청을 처리 중입니다. 잠시 후 결과를 확인하세요.")
        
        # 착용샷 생성 작업 완료 확인
        if check_task_status(sketc_id):
            wear_shot_data = get_task_result(sketc_id, 'result2')
            if wear_shot_data:
                wear_shot_image = Image.open(io.BytesIO(wear_shot_data))
                st.image(wear_shot_image, caption='착용샷', use_column_width=True)
                st.session_state.page = 'view_wear_video'  # 착용 영상 보기 페이지로 상태 변경
            else:
                st.error("착용샷을 생성할 수 없습니다.")
        else:
            st.error("착용샷 생성 작업이 시간 내에 완료되지 않았습니다. 나중에 다시 시도해주세요.")
        
     
    if st.button('아니요, 처음으로 돌아가기'):
        st.session_state.page = 'upload_sketch'
        
if st.session_state.page == 'view_wear_video':
    if st.button('움직이는 영상으로 확인하겠습니까?'):
        # 착용 영상 생성 작업 요청
        # wear_shot_id = st.session_state.task_id_for_wear_shot  # 착용샷 생성 작업 ID 사용
        task_send = celery_app.send_task('create_wear_video', args=[sketch_id], queue='animate_q')
        # st.session_state.task_id_for_wear_video = task_send.id  # 작업 ID 저장
        
        st.write("착용 영상 생성 요청을 처리 중입니다. 잠시 후 결과를 확인하세요.")
        
        # 착용 영상 생성 작업 완료 확인
        if check_task_status(sketch_id):
            wear_video_data = get_task_result(sketch_id, 'video')
            if wear_video_data:
               
                st.success("착용 영상이 생성되었습니다.")
                # 예: st.video('path_to_video_file_or_streaming_url')
            else:
                st.error("착용 영상을 생성할 수 없습니다.")
        else:
            st.error("착용 영상 생성 작업이 시간 내에 완료되지 않았습니다. 나중에 다시 시도해주세요.")
    if st.button('아니요, 처음으로 돌아가기'):
        st.session_state.page = 'upload_sketch'


