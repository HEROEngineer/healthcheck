from django import forms


class LowercaseEmailField(forms.EmailField):

    def clean(self, value):
        value = super(LowercaseEmailField, self).clean(value)
        return value.lower()


class EmailPasswordForm(forms.Form):
    email = LowercaseEmailField()
    password = forms.CharField(required=False)


class ReportSettingsForm(forms.Form):
    reports_allowed = forms.BooleanField(required=False)


class SetPasswordForm(forms.Form):
    password = forms.CharField()
