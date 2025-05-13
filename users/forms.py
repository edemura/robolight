from django import forms
from .models import Sequences
from .models import TubeType


class BroadcastForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    broadcast_text = forms.CharField(widget=forms.Textarea)


ch = [[1, 'ЦКДЛ'], [2, 'Внутренняя лаборатория']]



class OrdersForm(forms.Form):
    #tube_type=TubeType.make_choices()[0]
    
    tube_type1=forms.IntegerField(max_value=10, min_value=0, label="TubeType.make_choices()[0]")
    #tube_type2=forms.IntegerField(max_value=10, min_value=0, label=TubeType.make_choices()[1])  
    #tube_type3=forms.IntegerField(max_value=10, min_value=0, label=TubeType.make_choices()[2])  
    
    destination = forms.ChoiceField(choices=Sequences.make_choices(), label='Для направления в ')