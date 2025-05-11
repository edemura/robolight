from django import forms


class BroadcastForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    broadcast_text = forms.CharField(widget=forms.Textarea)


class OrdersForm(forms.Form):
    tube_number = forms.IntegerField(max_value=10, min_value=0)