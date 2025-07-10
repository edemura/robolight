"""
    Celery tasks. Some of them will be launched periodically from admin panel via django-celery-beat
"""

import time
from typing import Union, List, Optional, Dict

import telegram

from dtb.celery import app
from celery.utils.log import get_task_logger
from tgbot.handlers.broadcast_message.utils import send_one_message, from_celery_entities_to_entities, \
    from_celery_markup_to_markup
import os
from pathlib import Path
import logging

logger = get_task_logger(__name__)


@app.task(ignore_result=True)
def broadcast_message(
    user_ids: List[Union[str, int]],
    text: str,
    entities: Optional[List[Dict]] = None,
    reply_markup: Optional[List[List[Dict]]] = None,
    sleep_between: float = 0.4,
    parse_mode=telegram.ParseMode.HTML,
) -> None:
    """ It's used to broadcast message to big amount of users """
    logger.info(f"Going to send message: '{text}' to {len(user_ids)} users")

    entities_ = from_celery_entities_to_entities(entities)
    reply_markup_ = from_celery_markup_to_markup(reply_markup)
    for user_id in user_ids:
        try:
            send_one_message(
                user_id=user_id,
                text=text,
                entities=entities_,
                parse_mode=parse_mode,
                reply_markup=reply_markup_,
            )
            logger.info(f"Broadcast message was sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}, reason: {e}")
        time.sleep(max(sleep_between, 0.1))

    logger.info("Broadcast finished!")


#мое
    
from celery import shared_task
from users.models import Incomejson, TaskJson, Robo7Task, Analysis, AnalysisSet, TrayTube, Filename, Label, ManualTask, Task_source
from time import sleep
from datetime import datetime

#@shared_task()
@app.task(ignore_result=True)
def make_true():
    for i in Incomejson.objects.all():
        if i.is_processed==True:
            i.is_task_set=True
            i.save()
            
        else:
            i.is_task_set=False
            i.save()
    
#Создание из JSON экземпляра типа задание для ROBO7   
@app.task(ignore_result=True)
def make_robo7Task():
    for i in TaskJson.objects.exclude(is_task_set=True):
        try:
            task=Robo7Task()
            task.patient_fio=i.last_name+' '+i.first_name+' '+i.middle_name
            task.analysis=i.analysis_name
            task.code=i.barcode
            task.create_datetime=datetime.now()
            # Set task source for JSON API
            task.task_source = Task_source.objects.get(source_name="JSON API")
            task.save()
            i.is_task_set=True
            i.save()
        except Exception as e:
            i.is_task_set=False
            i.exception_text=f"Failed to make task {type(e)}, reason: {e}"
            i.save()


#Создание из экземпляра ManualTask типа задание для ROBO7   
@app.task(ignore_result=True)
def make_robo7Task_manual():
    for i in ManualTask.objects.exclude(is_task_set=True):
        try:
            task=Robo7Task()
            task.patient_fio=i.last_name+' '+i.first_name
            task.analysis=i.analysis
            #i.get_analysis_name()
            #Analysis.objects.get(pk=i.analysis).analysis_name
            task.code=i.barcode
            task.create_datetime=datetime.now()
            # Set task source for manual input
            task.task_source = Task_source.objects.get(source_name="Ручной ввод")
            task.save()
            i.is_task_set=True
            i.save()
        except Exception as e:
            i.is_task_set=False
            i.exception_text=f"Failed to make task {type(e)}, reason: {e}"
            i.save() 



#Присвоение заданиям номеров лотков, в которых находится подходящий тип пробирки
@app.task(ignore_result=True)
def tray_assign():
    for i in Robo7Task.objects.exclude(is_tray_assigned=True):
        try:
            an=Analysis.objects.filter(set=AnalysisSet.objects.get(active=True), analysis_name=i.analysis)
            tube_type=an[0].tube_type
            tray_tube=TrayTube.objects.filter(tube_type=tube_type)[0]
            if tray_tube!=None:
                i.tray_num=tray_tube.tray
                i.is_tray_assigned=True
                i.is_validated=True
                i.queue_calculate()
                
            else:
                i.is_tray_assigned=False
                i.exception_text=f"Для вида исследования {i.analysis}, не найдено доступных видов пробирок"
            i.save()
        except Exception as e:
            i.is_tray_assigned=False
            i.is_validated=True
            i.exception_text=f"Failed to assign tray {type(e)}, reason: {e}"
            i.save()


#Формирование имени файла
@app.task(ignore_result=True)
def filename_generate():
    for i in Robo7Task.objects.filter(is_validated=True):
        try:
            
            name=Filename()
            name.date=datetime.now().strftime('%m%d')
            name.stocker_code='0'+str(i.tray_num)
            #Описать смысл следующей строки
            name.tray_number=(4-len(str(i.queue_num)))*'0'+str(i.queue_num)
            name.patient_id=i.code
            name.patient_name=i.patient_fio
            an=Analysis.objects.filter(set=AnalysisSet.objects.get(active=True), analysis_name=i.analysis)[0]
            name.container_name=an.analysis_name_en

            filename=name.make()
            filenameok=name.makeok()
        
            if filename!=None:
                i.filename=filename
                i.filenameok=filenameok
                i.is_filename=True
                i.save()
            else:
                i.is_filename=False
                i.save()
        except Exception as e:    
            
            i.is_filename=False
            i.exception_text=f"Failed to make filename {type(e)}, reason: {e}"
            i.save()

#Формирование этикетки
@app.task(ignore_result=True)
def label_generate():
    
    for i in Robo7Task.objects.filter(is_validated=True):
        try:
            label=Label()
            label.barcode_data=i.code


            labeltext=label.make()
            

            if labeltext!=None:
                i.label=labeltext
                i.is_label=True
                i.save()
            else:
                i.is_label=False
                i.save()
        except Exception as e:
            i.is_label=False
            i.exception_text=f"Failed to make label {type(e)}, reason: {e}"
            i.save()

#Отправка задания на robo7
@app.task(ignore_result=True)
def send_to_robo7():
    
    #folder='out'
    #folder=r'C:\\robo7_data\PRINT\DATA'
    folder=Path('DATA/')

    for i in Robo7Task.objects.filter(is_filename=True, is_label=True, is_sent=(False or None)):
            
        file_to_open_dat=folder / (i.filename+'.dat')
        file_to_open_def=folder / (i.filename+',DEF.TXT')

        try:    
            if not os.path.exists(file_to_open_dat):
                with open(file_to_open_dat,'w') as file:
                    file.write(i.label)
                    file.close()
            if not os.path.exists(file_to_open_def):
                with open(file_to_open_def,'w') as file:
                    file.write('')
                    file.close()

            i.is_sent=True
            i.save()
        except Exception as e:
            i.is_sent=False
            i.exception_text=f"Failed to send file to robo7 {type(e)}, reason: {e}"
            i.save()


#Проверка выполнения задач прибором
@app.task(ignore_result=True)
def check_robo7_complete():
    
    folder=Path('DATA/')
    for i in Robo7Task.objects.filter(is_sent=True, is_complete=(False or None)):
        
        file_to_open_ok=folder / (i.filenameok+'.txt')
        file_to_open_dat=folder / (i.filename+'.dat')
        file_to_open_def=folder / (i.filename+',DEF.TXT')

        #path=r'C:\\roboweb\robo7tools\webadmin\get'
        #path=r'C:\\robo7_data\PRINT\DATA'
        
        if len(os.listdir(path=folder))!=0:
                
            #for filename in os.listdir(path=path):
            
                if os.path.exists(file_to_open_ok):
                    # if os.path.exists(file_to_open_dat):
                    #     try:
                    #         os.remove(file_to_open_dat)
                    #     except:
                    #         pass

                    # if os.path.exists(file_to_open_def):
                    #     try:
                    #         os.remove(file_to_open_def)
                    #     except:
                    #         pass
                        
                    try:    
                        # os.remove(file_to_open_ok)

                        i.is_complete=True
                        i.save()
                    except Exception as e:
                        i.is_complete=False
                        i.exception_text=f"Failed to recieve result from robo7 {type(e)}, reason: {e}"
                        i.save()


#удаление всех файлов в папке дата
@app.task(ignore_result=True)
def remove_all_data():

    folder=Path('DATA/')
    

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            pass
            #print(f'Ошибка при удалении файла {file_path}. {e}')
    

# Создание задания для ROBO7 из Orders
@app.task(ignore_result=True)
def R7FromOrders(order_id):
    from users.models import Orders, Robo7Task, Task_source, Tube_qty
    from datetime import datetime
    import traceback
    try:
        order = Orders.objects.get(pk=order_id)
        tubes = Tube_qty.objects.filter(order_id=order)
        task_source = Task_source.objects.get(source_name="Order")
        for tube in tubes:
            # You may want to customize these fields based on your business logic
            Robo7Task.objects.create(
                patient_fio=f"Order #{order.id}",
                analysis=str(tube.tube_type_id),
                code=f"ORDER-{order.id}-TUBE-{tube.tube_type_id.id}",
                create_datetime=datetime.now(),
                task_source=task_source
            )
            logger.info(f"Created Robo7Task for order {order.id}, tube {tube.tube_type_id}")
    except Exception as e:
        logger.error(f"Failed to create Robo7Task from Orders {order_id}: {e}\n{traceback.format_exc()}") 