from django.forms.widgets import TextInput, DateInput, DateTimeInput, TimeInput

class HTML5EmailInput(TextInput):
    input_type = 'email'

class HTML5NumberInput(TextInput):
    input_type = 'number'

class HTML5DateInput(DateInput):
    input_type = 'date'

class HTML5DateTimeInput(DateTimeInput):
    input_type = 'datetime'

class HTML5TimeInput(TimeInput):
    input_type = 'time'
