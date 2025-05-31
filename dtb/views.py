import json
import logging
from django.views import View
from django.http import JsonResponse, HttpResponse
from telegram import Update

from dtb.celery import app
from dtb.settings import DEBUG
from tgbot.dispatcher import dispatcher
from tgbot.main import bot

from users.models import Incomejson
from users.models import Orders
from users.models import TubeType
from users.models import Post_data
from users.models import Sequences
from users.models import Tube_qty
from django.core import serializers

from django.shortcuts import render

from users.forms import OrdersForm
from django.http import HttpResponseRedirect

logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


def index(request):
    return JsonResponse({"error": "sup hacker"})


class TelegramBotWebhookView(View):
    # WARNING: if fail - Telegram webhook will be delivered again.
    # Can be fixed with async celery task execution
    def post(self, request, *args, **kwargs):
        if DEBUG:
            process_telegram_event(json.loads(request.body))
        else:
            # Process Telegram event in Celery worker (async)
            # Don't forget to run it and & Redis (message broker for Celery)!
            # Locally, You can run all of these services via docker-compose.yml
            process_telegram_event.delay(json.loads(request.body))

        # e.g. remove buttons, typing event
        return JsonResponse({"ok": "POST request processed"})

    def get(self, request, *args, **kwargs):  # for debug
        return JsonResponse({"ok": "Get request received! But nothing done"})

#добавлено мной

from json import loads
def recieve_json(request):
    if request.method == 'POST':
        #print(loads(request.body)['name'])
        json=Incomejson()
        #logger.info(request.body)
        #print("Goodbye cruel world!", file="stderr.txt")
        #data = serializers.serialize("json", request.body)
        json.text=request.body
        json.save()
        #json.process()

    return JsonResponse({"ok": "JSON received"})

#DRF

from users.models import Incomejson
from rest_framework import permissions, viewsets

from users.serializers import IncomeJsonSerializer


class IncomeJsonViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Incomejson.objects.all().order_by('-create_datetime')
    serializer_class = IncomeJsonSerializer
    permission_classes = [permissions.IsAuthenticated]



#пробуем создать вью для файлов

from users.models import DataFile

def data_files(request):
    DataFile.delete_data()
    DataFile.read_data()
    files_list = DataFile.objects.all()
    output = ", ".join([q.file for q in files_list])
    return HttpResponse(output)

#пробуем создать вью для ORDERS

from users.models import Orders

def orders_request(request):
    if request.method == "POST":
        form = OrdersForm(request.POST)
        data = Post_data()
        data.text = request.POST
        data.save()
        
        if form.is_valid():
            order = Orders()
            order.sequence_id = Sequences.objects.get(pk=form.cleaned_data['destination'])
            order.total_tubes_qty = 0
            order.save()
            
            # Process each tube quantity
            tubes = TubeType.objects.all()
            for tube in tubes:
                tube_id = str(tube.id)
                if tube_id in request.POST:
                    qty = int(request.POST[tube_id])
                    if qty > 0:  # Only create entries for non-zero quantities
                        tube_qty = Tube_qty(
                            order_id=order,
                            tube_type_id=tube,
                            tube_qty=qty
                        )
                        tube_qty.save()
                        order.total_tubes_qty += qty
            
            order.save()

            #Тут мы должны сослаться на таск, который создаст Robo7Task

        return HttpResponseRedirect("/orders/")
    else:
        form = OrdersForm()
        tubes = TubeType.objects.all()
    return render(request, "order.html", {"form": form, "tubes": tubes})

