from django import forms
from .models import Sequences


class BroadcastForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    broadcast_text = forms.CharField(widget=forms.Textarea)


ch = [[1, 'ЦКДЛ'], [2, 'Внутренняя лаборатория']]



class OrdersForm(forms.Form):
    tube_number = forms.IntegerField(max_value=10, min_value=0)
    destination = forms.ChoiceField(choices=Sequences.make_choices(), label='Для направления в ')