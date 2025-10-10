from django import forms
from .models import Sequences
from .models import TubeType


class BroadcastForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    broadcast_text = forms.CharField(widget=forms.Textarea)


class ButtonGroupWidget(forms.RadioSelect):
    template_name = 'widgets/button_group.html'
    option_template_name = 'widgets/button_group_option.html'


ch = [[1, 'ЦКДЛ'], [2, 'Внутренняя лаборатория']]



class OrdersForm(forms.Form):
    #tube_type=TubeType.make_choices()[0]
    
    #tube_type1=forms.IntegerField(max_value=10, min_value=0, label="TubeType.make_choices()[0]")
    #tube_type2=forms.IntegerField(max_value=10, min_value=0, label=TubeType.make_choices()[1])  
    #tube_type3=forms.IntegerField(max_value=10, min_value=0, label=TubeType.make_choices()[2])  
    
    destination = forms.ChoiceField(
        choices=[],
        label='Для направления в',
        widget=ButtonGroupWidget(),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load choices lazily to avoid database queries during module import
        try:
            self.fields['destination'].choices = Sequences.make_choices()
        except Exception:
            # If database is not available, use empty choices
            self.fields['destination'].choices = []