from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.translation import gettext_lazy as _

from . import models


class AmortizationAdminInline(admin.TabularInline):
    """
    Admin inline view for :model:`lending.Amortization`
    """
    model = models.Amortization


class LoanSourceAdminInline(admin.StackedInline):
    """
    Admin inline view for :model:`lending.LoanSource`
    """
    model = models.LoanSource
    extra = 1
    max = 2


@admin.register(models.Bank)
class BankAdmin(admin.ModelAdmin):
    """
    Admin view for :model:`lending.Bank`
    """
    list_display = ("name", "abbreviation")


@admin.register(models.Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    """
    Admin view for :model:`lending.Borrower`
    """
    pass


@admin.register(models.CapitalSource)
class CapitalSourceAdmin(admin.ModelAdmin):
    """
    Admin view for :model:`lending.CapitalSource`
    """
    list_display = ("name", "source", "bank")

    def source(self, obj) -> str:
        return obj.get_source_display()


@admin.register(models.Loan)
class LoanAdmin(admin.ModelAdmin):
    """
    Admin view for :model:`lending.Loan`
    """
    list_display = (
        "borrower",
        "amount_display",
        "interest_rate_display",
        "interest_amount",
        "term",
        "loan_date",
        "is_completed",
    )
    list_filter = ("borrower", "is_completed")
    search_fields = ("borrower__first_name", "borrower_last_name")
    inlines = [LoanSourceAdminInline, AmortizationAdminInline]

    def amount_display(self, obj):
        return intcomma(obj.amount)
    amount_display.short_description = _("Amount")

    def interest_amount(self, obj):
        return intcomma(obj.interest_amount)

    def interest_rate_display(self, obj):
        return f"{obj.interest_rate}%"
    interest_rate_display.short_description = _("Interest Rate")
