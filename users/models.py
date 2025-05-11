from __future__ import annotations

from typing import Any, Union, Optional, Tuple

from django.db import models
from django.db.models import QuerySet, Manager
from django.utils.translation import gettext_lazy as _

from telegram import Update
from telegram.ext import CallbackContext

from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager

from dtb.celery import app
from pathlib import Path
import os


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)

    is_blocked_bot = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)

    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():  # you can't invite yourself
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"


class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = GetOrNoneManager()

    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"


#Все что ниже самописное для робо7
    
#Задачи robo7

class Robo7Task(models.Model):
  
  class Meta:
     verbose_name=_('Задание для BC ROBO7')
     verbose_name_plural=_('Задания для BC ROBO7')

  patient_fio = models.CharField(max_length=255, verbose_name="ФИО пациента")
  analysis = models.CharField(max_length=255, verbose_name="Наименование вида исследования")
  code = models.CharField(max_length=255, verbose_name="ШК")
  tray_num = models.IntegerField(null=True, default=0, verbose_name="Назначенный лоток")
  queue_num = models.IntegerField(null=True, default=1, verbose_name="Номер последовательности")
  is_tray_assigned = models.BooleanField(null=True, default=None, verbose_name="Лоток назначен")
  is_validated = models.BooleanField(null=True, default=None, verbose_name="Валидация пройдена")
  is_sent = models.BooleanField(null=True, default=None, verbose_name="Отправлено на прибор")
  is_complete = models.BooleanField(null=True, default=None, verbose_name="Выполнено")
  is_filename = models.BooleanField(null=True, default=None, verbose_name="Сформировано имя файла")
  filename = models.CharField(max_length=255, null=True, default=None, verbose_name="Имя файла")
  filenameok = models.CharField(max_length=255, null=True, default=None, verbose_name="Имя файла OK")
  is_label = models.BooleanField(null=True, default=None, verbose_name="Сформировано содержание этикетки")
  label = models.CharField(max_length=255, null=True, default=None, verbose_name="Содержание этикетки")
  create_datetime = models.DateTimeField(null=True, auto_now=False, auto_now_add=True, verbose_name='Создано')
  update_datetime = models.DateTimeField(null=True, auto_now=True, auto_now_add=False, verbose_name='Изменено')
  tray_num_task = models.IntegerField(null=True, default=0, verbose_name="tray num за текущую дату")
  exception_text=models.TextField(null=True, default=None, verbose_name="Ошибка")

  def __str__(self):
    return self.patient_fio+' '+self.code+' '+str(self.create_datetime)
  
  #расчет номера последовательности. Если новая дата. то нумерация стартует заново
  def queue_calculate(self):
     
     spk=self.pk
     
     #get_previous_by_
     #get_previous_by_create_datetime(pk__lt=spk)

     prev=__class__.objects.filter(id__lt=spk).order_by('-id').only('id').first()
    
     #prev=__class__.objects.get(pk=spk-1)
     if self.create_datetime.date()==prev.create_datetime.date():
        self.queue_num=prev.queue_num+1
     else: 
        self.queue_num=1
    
    
     self.save()
  
  #Вычитает день из даты создания для экземпляра - для тестирования
  def past_date(self):
     from datetime import timedelta
     self.create_datetime=self.create_datetime - timedelta(days=1)
     self.save()

  
  #Удалить файлы с диска для инстанса
  def delete_data(self):
    
    folder=Path('DATA/')
    for i in Robo7Task.objects.filter(is_sent=True, is_complete=(False or None)):
        
        file_to_open_ok=folder / (i.filenameok+'.txt')
        file_to_open_dat=folder / (i.filename+'.dat')
        file_to_open_def=folder / (i.filename+',DEF.TXT')

        #path=r'C:\\roboweb\robo7tools\webadmin\get'
        #path=r'C:\\robo7_data\PRINT\DATA'
                
            #for filename in os.listdir(path=path):
            
        if os.path.exists(file_to_open_ok):
            try:
                os.remove(file_to_open_ok)
            except:
                pass
        if os.path.exists(file_to_open_dat):
            try:
                os.remove(file_to_open_dat)
            except:
                pass

        if os.path.exists(file_to_open_def):
            try:
                os.remove(file_to_open_def)
            except:
                pass
            
        try:    

            i.is_complete=True
            i.save()
        except Exception as e:
            i.is_complete=False
            i.exception_text=f"Failed to delete results from DATA folder {type(e)}, reason: {e}"
            i.save()

#входящий JSON неразобранный тестовый

class Incomejson(models.Model):

    class Meta:
        verbose_name=_('Входящие JSON тест')
        verbose_name_plural=_('Входящие JSON тест')

    create_datetime = models.DateTimeField(null=True, auto_now=False, auto_now_add=True, verbose_name='Создано')
    is_processed = models.BooleanField(null=True, default=None, verbose_name="Валидация пройдена")
    is_task_set = models.BooleanField(null=True, default=None, verbose_name="создан таск")
    json = models.JSONField(null=True, default=None, encoder=None, decoder=None)
    text = models.TextField(null=True, default=None)

    def __str__(self):
        return str(self.create_datetime)
    
    @app.task(ignore_result=True)
    def process(self):
        self.is_processed=True

    def undo(self):
        self.is_processed=False


#входящий JSON неразобранный таск
# Добавить сериализатор и обработку апи

class TaskJson(models.Model):

    class Meta:
        verbose_name=_('Входящие JSON')
        verbose_name_plural=_('Входящие JSON')

    create_datetime = models.DateTimeField(null=True, auto_now=False, auto_now_add=True, verbose_name='Создано')
    is_task_set = models.BooleanField(null=True, default=None, verbose_name="создан таск")

    first_name=models.TextField(null=True, default=None, verbose_name="Имя пациента")
    last_name=models.TextField(null=True, default=None, verbose_name="Фамилия пациента")
    middle_name=models.TextField(null=True, default=None, verbose_name="Отчество пациента")
    analysis_name=models.TextField(null=True, default=None, verbose_name="Наименование исследования")
    analysis_code=models.TextField(null=True, default=None, verbose_name="Код исследования")
    barcode=models.TextField(null=True, default=None, verbose_name="Штрих-код")
    exception_text=models.TextField(null=True, default=None, verbose_name="Ошибка")

    def __str__(self):
        return str(self.create_datetime)



#имя файла для задания
class Filename:
    template='{terminal_host},{terminal_robo7},{date},{tray_number},{last_tube},{seq_tray},{queue},{patient_id},{patient_name},{container_name},{sample_volume},{department_name},{number_of_labels},{stocker_code},{rfid},{priority}'
    templateok='{terminal_host},{terminal_robo7},{date},{tray_number},OK'
    terminal_host='0005'
    terminal_robo7='0001'
    date='1213'
    #tray_number='0032'
    tray_number='0001'
    last_tube='9'
    seq_tray='01'
    queue='1234'
    patient_id='0123456789'
    patient_name='Ivan Petrov'
    container_name='HbA1c'
    sample_volume='1.0'
    department_name='Pediatrics'
    number_of_labels='1'
    stocker_code='01'
    rfid=''
    priority='0'
    

    def make(self):
       tmpl=self.template.format(terminal_host=self.terminal_host,
                                 terminal_robo7=self.terminal_robo7,
                                 date=self.date,
                                 tray_number=self.tray_number,
                                 last_tube=self.last_tube,
                                 seq_tray=self.seq_tray,
                                 queue=self.queue,
                                 patient_id=self.patient_id,
                                 patient_name=self.patient_name,
                                 container_name=self.container_name,
                                 sample_volume=self.sample_volume,
                                 department_name=self.department_name,
                                 number_of_labels=self.number_of_labels,
                                 stocker_code=self.stocker_code,
                                 rfid=self.rfid,
                                 priority=self.priority)
       
       return tmpl
    
    def makeok(self):
       tmpl=self.templateok.format(terminal_host=self.terminal_host,
                                 terminal_robo7=self.terminal_robo7,
                                 date=self.date,
                                 tray_number=self.tray_number,
                                 )
       
       return tmpl


# Содержимое файла для задания
class Label:
   template='BAR|{x_pos}^{y_pos}^{height}^{barcode_type}^{code_type}^{narrow_width}^{wide_width}^{check_digit}^{draw_direction}^{barcode_data}|CR'
   x_pos='2'
   y_pos='2'
   height='15'
   barcode_type='7'
   code_type='1'
   narrow_width='4'
   wide_width='8'
   check_digit='1'
   draw_direction='0'
   barcode_data='11111'

   def make(self):
      lbl=self.template.format(x_pos=self.x_pos,                         
            y_pos=self.y_pos,
            height=self.height,
            barcode_type=self.barcode_type,
            code_type=self.code_type,
            narrow_width=self.narrow_width,
            wide_width=self.wide_width,
            check_digit=self.check_digit,
            draw_direction=self.draw_direction,
            barcode_data=self.barcode_data)
      return lbl


# Наборы исследований

class AnalysisSet(models.Model):
  
  class Meta:
     verbose_name=_('Набор исследования')
     verbose_name_plural=_('Наборы исследования')

  set = models.CharField(max_length=255, verbose_name="Наборы исследований")
  active = models.BooleanField(null=False, default=False, verbose_name="Активный набор")   

  def __str__(self):
    return self.set

# Типы пробирок

class TubeType(models.Model):

  class Meta:
     verbose_name=_('Тип пробирки')
     verbose_name_plural=_('Виды пробирок')
  
  volume = models.CharField(max_length=255, verbose_name="Объем")
  color = models.CharField(max_length=255, verbose_name="Цвет")
  filler = models.CharField(max_length=255, verbose_name="Наполнитель")
  def __str__(self):
    return self.volume+' '+self.color+' '+self.filler


# Пробирки в лотках

class TrayTube(models.Model):

  class Meta:
     verbose_name=_('Лоток')
     verbose_name_plural=_('Расположение видов пробирок в лотках')

  set = models.ForeignKey(
        "users.AnalysisSet",
        on_delete=models.CASCADE,
        verbose_name="Набор исследований"
    )

  tube_type = models.ForeignKey(
        "users.TubeType",
        on_delete=models.CASCADE,
        verbose_name="Тип пробирок"
    )
  
  tray = models.IntegerField(unique=True, verbose_name="Номер лотка")

  def __str__(self):
    return '#'+str(self.tray)

# Исследования        

class Analysis(models.Model):

  class Meta:
     verbose_name=_('Вид исследования')
     verbose_name_plural=_('Виды исследований')

  set = models.ForeignKey(
        "users.AnalysisSet",
        on_delete=models.CASCADE,
        verbose_name="Набор исследований"
    )
  tube_type = models.ForeignKey(
      "users.TubeType",
      on_delete=models.CASCADE,
      verbose_name="Тип пробирки"
  )
  analysis_name = models.CharField(max_length=255, default="Новый вид исследования", verbose_name="Вид исследования(наименование)")
  analysis_code = models.CharField(max_length=255, default="Новый код исследования", verbose_name="Вид исследования(Код)")
  analysis_name_en = models.CharField(max_length=255, default="name", verbose_name="Для печати (англ)")
  
  def __str__(self):
    return self.analysis_name
  


  #Ручная отправка заданий
# Добавить сериализатор и обработку апи

class ManualTask(models.Model):

    class Meta:
        verbose_name=_('Ручная отправка - задания')
        verbose_name_plural=_('Ручная отправка заданий')

    create_datetime = models.DateTimeField(null=True, auto_now=False, auto_now_add=True, verbose_name='Создано')
    is_task_set = models.BooleanField(null=True, default=None, verbose_name="создан таск")

    first_name=models.TextField(null=True, default=None, verbose_name="Имя пациента")
    last_name=models.TextField(null=True, default=None, verbose_name="Фамилия пациента")
    analysis=models.ForeignKey(
        "users.Analysis",
        on_delete=models.CASCADE,
        verbose_name="Вид исследования"
    )
    barcode=models.TextField(null=True, default=None, verbose_name="Штрих-код")
    exception_text=models.TextField(null=True, default=None, verbose_name="Ошибка")

    def __str__(self):
        return str(self.create_datetime)
    
    def get_analysis_name(self):
       return Analysis.objects.get(pk=self.analysis).analysis_name
    

class DataFile(models.Model):
    class Meta:
        verbose_name=_('Файлы')
        verbose_name_plural=_('Содержимое папки DATA')

    file=models.TextField(null=True, default=None, verbose_name="Имя файла")
    
    @classmethod
    def read_data(cls):
        folder=Path('DATA/')
    

        for filename in os.listdir(folder):
           datafile = __class__()
           datafile.file = filename
           datafile.save()
            # file_path = os.path.join(folder, filename)
            # try:
            #     if os.path.isfile(file_path):
            #         os.remove(file_path)
            # except Exception as e:
            #     pass
            #     #print(f'Ошибка при удалении файла {file_path}. {e}')
           
    @classmethod
    def delete_data(cls):

        for inst in __class__.objects.all():
           inst.delete()

#DataFile.delete_data()           
#DataFile.read_data()

#Заказы - моделька для тестирования вывода в форму
# поля: тип последовательности ШК, номер шк,     
    
class Sequences(models.Model):
    class Meta:
        verbose_name=_('Последовательность нумерации')
        verbose_name_plural=_('Последовательности нумерации')

    sequence_name=models.CharField(null=True, default=None, verbose_name="Наименование последовательности")
    is_active=models.BooleanField(null=False, default=False, verbose_name="Последовательность активна")
    digits_number=models.IntegerField(null=False, verbose_name="Количество знаков(длина последовательности)")
    current_number=models.IntegerField(null=True, verbose_name="Текущее значение")

    def __str__(self):
        return str(self.sequence_name)


class Orders(models.Model):
    class Meta:
        verbose_name=_('Заказ')
        verbose_name_plural=_('Заказы')

    sequence_id=models.ForeignKey(
       "users.Sequences",
       null=True, 
       default=None,
        on_delete=models.CASCADE,
        verbose_name="Вид последовательности"
    )

    tube_type = models.ForeignKey(
      "users.TubeType",
      on_delete=models.CASCADE,
      verbose_name="Тип пробирки"
  )

    barcode_type=models.TextField(null=True, default=None, verbose_name="Тип ШК")
    barcode_number=models.TextField(null=True, default=None, verbose_name="Номер ШК")

    
    #file=models.TextField(null=True, default=None, verbose_name="Имя файла")

class Tube_qty(models.Model):
    class Meta:
        verbose_name=_('Пробирки в заказе')
        verbose_name_plural=_('Пробирки в заказе')

    order_id=models.ForeignKey(
       "users.Orders",
       null=True, 
       default=None,
        on_delete=models.CASCADE,
        verbose_name="Номер заказа"
    )

    tube_type_id=models.ForeignKey(
       "users.TubeType",
       null=True, 
       default=None,
        on_delete=models.CASCADE,
        verbose_name="Вид пробирки"
    )

    tube_qty = models.IntegerField(
        null=True, 
       default=1,
       verbose_name="Количество")
    