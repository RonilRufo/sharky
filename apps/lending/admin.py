from dateutil.relativedelta import relativedelta

from django.contrib import admin, messages
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
    actions = ["generate_amortization"]
    list_display = (
        "borrower",
        "amount_display",
        "interest_rate_display",
        "interest_amount",
        "interest_gained",
        "term",
        "loan_date",
        "is_completed",
    )
    list_filter = ("borrower", "is_completed")
    search_fields = ("borrower__first_name", "borrower_last_name")
    inlines = [LoanSourceAdminInline, AmortizationAdminInline]

    def amount_display(self, obj):
        amount = int(obj.amount) if obj.amount % 1 == 0 else obj.amount
        return intcomma(amount)
    amount_display.short_description = _("Amount")

    def interest_amount(self, obj):
        amount = (
            int(obj.interest_amount)
            if obj.interest_amount % 1 == 0 else obj.interest_amount
        )
        return intcomma(amount)

    def interest_rate_display(self, obj):
        amount = (
            int(obj.interest_rate) if obj.interest_rate % 1 == 0 else obj.interest_rate
        )
        return f"{amount}%"
    interest_rate_display.short_description = _("Interest Rate")

    def interest_gained(self, obj):
        amount = (
            int(obj.interest_gained)
            if obj.interest_gained % 1 == 0 else obj.interest_gained
        )
        return intcomma(amount)

    def generate_amortization(self, request, queryset):
        """
        Generates the amortization for the selected loans.
        """
        for loan in queryset:
            # The number of amortization will depend on whether the payment schedule is
            # monthly or bi-monthly. If monthly, then the number of amortization will be
            # equal to the loan's term. If bi-monthly, it means there will be 2 payments
            # for each month which should be equal to twice the value of term.
            count = loan.term if loan.is_payment_schedule_monthly else loan.term * 2

            amortization = []
            due_date = loan.first_payment_date
            for schedule in range(count):
                amortization.append(
                    models.Amortization(
                        loan=loan,
                        amount_due=loan.amortization_amount_due,
                        due_date=due_date,
                    )
                )

                if loan.is_payment_schedule_monthly:
                    due_date += relativedelta(months=1)
                else:
                    due_date += relativedelta(days=15)

            if len(amortization) > 0:
                models.Amortization.objects.bulk_create(amortization)

        messages.success(request, _("Successfully generated amortization."))
    generate_amortization.short_description = _("Generate Loan Amortization")
