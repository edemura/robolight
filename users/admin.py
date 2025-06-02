from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render

from dtb.settings import DEBUG

from users.models import Location
from users.models import User
from users.models import Robo7Task
from users.models import Incomejson
from users.models import TaskJson
from users.models import ManualTask
from users.models import Orders
from users.models import Sequences
from users.models import Tube_qty
from users.models import Post_data
from users.models import Task_source

from users.models import TubeType, TrayTube, Analysis, AnalysisSet, DataFile

from users.forms import BroadcastForm

from users.tasks import broadcast_message
from tgbot.handlers.broadcast_message.utils import send_one_message


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'username', 'first_name', 'last_name', 
        'language_code', 'deep_link',
        'created_at', 'updated_at', "is_blocked_bot",
    ]
    list_filter = ["is_blocked_bot", ]
    search_fields = ('username', 'user_id')

    actions = ['broadcast']

    def broadcast(self, request, queryset):
        """ Select users via check mark in django-admin panel, then select "Broadcast" to send message"""
        user_ids = queryset.values_list('user_id', flat=True).distinct().iterator()
        if 'apply' in request.POST:
            broadcast_message_text = request.POST["broadcast_text"]

            if DEBUG:  # for test / debug purposes - run in same thread
                for user_id in user_ids:
                    send_one_message(
                        user_id=user_id,
                        text=broadcast_message_text,
                    )
                self.message_user(request, f"Just broadcasted to {len(queryset)} users")
            else:
                broadcast_message.delay(text=broadcast_message_text, user_ids=list(user_ids))
                self.message_user(request, f"Broadcasting of {len(queryset)} messages has been started")

            return HttpResponseRedirect(request.get_full_path())
        else:
            form = BroadcastForm(initial={'_selected_action': user_ids})
            return render(
                request, "admin/broadcast_message.html", {'form': form, 'title': u'Broadcast message'}
            )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'created_at']


#Все что ниже самописное для робо7

@admin.action(description="Created -1 day")
def past_date(modeladmin, request, queryset):
     for i in queryset:
         i.past_date()
     #queryset.update(past_date())
         
@admin.action(description="Delete data & mark as complete")
def delete_data(modeladmin, request, queryset):
     for i in queryset:
         i.delete_data()
     

@admin.register(Robo7Task) 
class Robo7TaskAdmin(admin.ModelAdmin):
    list_display=['task_source', 'patient_fio', 'analysis', 'code', 'tray_num', 'queue_num', 'is_tray_assigned',
                  'is_validated', 'filename', 'is_filename', 'label', 'is_label', 'is_sent', 'is_complete', 'update_datetime', 'create_datetime', 'filenameok','tray_num_task', 'exception_text']
    fieldsets = [
        (None, {"fields": ['task_source', 'patient_fio', 'analysis', 'code', 'tray_num', 'queue_num', 'is_tray_assigned',
                  'is_validated', 'filename', 'is_filename', 'label', 'is_label', 'is_sent', 'is_complete', 'update_datetime','create_datetime','filenameok','tray_num_task','exception_text']}),
        
    ]
    readonly_fields = ('create_datetime', 'update_datetime',)
    actions = [past_date, delete_data]
    list_per_page = 5

  
@admin.action(description="Mark selected stories as published")
def make_published(modeladmin, request, queryset):
    queryset.update(is_processed=True)  

@admin.action(description="Undo")
def make_undo(modeladmin, request, queryset):
    queryset.update(is_processed=False)  


@admin.register(Incomejson) 
class IncomejsonAdmin(admin.ModelAdmin):
    list_display = ['id','create_datetime', 'is_processed', 'is_task_set', 'text', 'json',]
    actions = [make_published, make_undo]

@admin.register(TaskJson) 
class TaskJsonAdmin(admin.ModelAdmin):
    list_display = ['id','create_datetime', 'is_task_set', 'first_name', 'last_name', 'middle_name', 'analysis_name', 'analysis_code', 'barcode', 'exception_text',]
    readonly_fields = ('create_datetime', 'exception_text', )

#Пробирки и все остальное
admin.site.register(TubeType)

class TrayTubeInline(admin.StackedInline):
    model = TrayTube
    extra = 3 

class AnalysisInline(admin.StackedInline):
    model = Analysis
    extra = 3 

class AnalysisSetAdmin(admin.ModelAdmin):
    
    list_display = ["set", "active"]
    fieldsets = [
        (None, {"fields": ["set", "active"]}),
        
    ]
    inlines = [AnalysisInline, TrayTubeInline]

admin.site.register(AnalysisSet, AnalysisSetAdmin) 

@admin.register(Analysis) 
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['analysis_name','analysis_code', 'analysis_name_en', 'set', 'tube_type',]

@admin.register(ManualTask) 
class ManualTaskAdmin(admin.ModelAdmin):
    list_display = ['id','create_datetime', 'is_task_set', 'first_name', 'last_name', 'analysis', 'barcode', 'exception_text', ]
    readonly_fields = ('create_datetime', 'exception_text', )


@admin.action(description="read_data")
def read_data(modeladmin, request, queryset):
    DataFile.read_data()  

@admin.register(DataFile) 
class DataFileAdmin(admin.ModelAdmin):
    list_display = ['file', ]
    actions = ['read_data']




# from dtb.urls import urlpatterns
# admin.site.get_urls(urlpatterns)
    
from django.urls import path

class MyAdminSite(admin.AdminSite):
    site_header = "Custom Administration"
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path("settings/", self.admin_view(self.settings_view), name="settings")]
        return my_urls + urls

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        if app_label is None or app_label == 'general':
            app_list.append(
                {
                    "name": "General",
                    "app_label": "general",
                    "models": [
                        {
                            "name": "Settings",
                            "object_name": "settings",
                            "admin_url": "/admin/settings",
                            "view_only": True,
                        }
                    ],
                }
            )
        return app_list

    # def settings_view(self, request):
    #     context = dict(self.each_context(request))
    #     context['parameters'] = config.get_parameters()
    #     return TemplateResponse(request, 'admin/settings/settings.html', context)

@admin.register(Sequences) 
class SequencesAdmin(admin.ModelAdmin):
    list_display = ['sequence_name','is_active', 'digits_number', 'current_number']

@admin.register(Tube_qty) 
class Tube_qtyAdmin(admin.ModelAdmin):
    list_display = ['order_id','tube_type_id', 'tube_qty']


class Tube_qtyInline(admin.StackedInline):
    model = Tube_qty
    extra = 3 

@admin.register(Orders) 
class OrdersAdmin(admin.ModelAdmin):
    list_display = ['create_datetime','sequence_id','total_tubes_qty']
    
    fieldsets = [
        (None, {"fields": ["sequence_id"]}),
        
    ]
    inlines = [Tube_qtyInline]


@admin.register(Post_data) 
class Post_dataAdmin(admin.ModelAdmin):
    list_display = ['text']

@admin.register(Task_source)
class Task_sourceAdmin(admin.ModelAdmin):
    list_display = ['source_name']
    search_fields = ['source_name']