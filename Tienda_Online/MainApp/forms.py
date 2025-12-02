from django import forms
from .models import Order

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        # Agregamos explicitamente el atributo HTML multiple
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class OrderRequestForm(forms.ModelForm):

    reference_images = forms.FileField(
        label='Imágenes de referencia (máximo 5)',
        required=False,
        widget=MultipleFileInput()
    )
    
    class Meta:
        model = Order
        fields = [
            'customer_name',
            'email',
            'phone',
            'product_ref',
            'description',
            'requested_date',
            'reference_images',   # 🔥 IMPORTANTE
        ]
        widgets = {
            'requested_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Teléfono o Red Social'
            }),
        }
