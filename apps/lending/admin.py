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


class CapitalSourcePaymentAdminInline(admin.TabularInline):
    """
    Admin inline view for :model:`lending.CapitalSourcePayment`
    """

    model = models.CapitalSourcePayment
    extra = 1
    min = 0
    max = 2


class LoanSourceAmortizationAdminInline(admin.TabularInline):
    """
    Admin inline view for :model:`lending.LoanSourceAmortization`
    """

    model = models.LoanSourceAmortization
    extra = 1
    max = 2


@admin.register(models.LoanSource)
class LoanSourceAdmin(admin.ModelAdmin):
    """
    Admin view for :model:`lending.LoanSource`
    """

    actions = ["generate_capital_source_payments"]
    model = models.LoanSource
    inlines = [CapitalSourcePaymentAdminInline, LoanSourceAmortizationAdminInline]
    list_display = (
        "capital_source",
        "get_source_name_from_capital_source",
        "loan",
        "monthly_amortization",
        "interest_rate",
    )
    list_filter = ("capital_source__source", "capital_source__bank")
    search_fields = ("capital_source__bank__name", "capital_source__name")

    def get_source_name_from_capital_source(self, obj):
        return obj.capital_source.get_source_display()

    get_source_name_from_capital_source.short_description = _("Source Type")

    def generate_capital_source_payments(self, request, queryset):
        """
        Generates capita source payments for the selected loan sources.
        """
        for source in queryset:
            # The number of payments will depend on whether the payment schedule is
            # monthly or bi-monthly. If monthly, then the number of payments will be
            # equal to the loan's term. If bi-monthly, it means there will be 2 payments
            # for each month which should be equal to twice the value of term.
            loan = source.loan
            count = loan.term if loan.is_payment_schedule_monthly else loan.term * 2

            payments = []
            due_date = loan.first_payment_date
            for schedule in range(count):
                payments.append(
                    models.CapitalSourcePayment(
                        loan_source=source,
                        amount=source.capital_source_payment_amount,
                        due_date=due_date,
                    )
                )

                if loan.is_payment_schedule_monthly:
                    due_date += relativedelta(months=1)
                else:
                    due_date += relativedelta(days=15)

            if payments:
                models.CapitalSourcePayment.objects.bulk_create(payments)

        messages.success(request, _("Successfully generated capital source payments."))

    generate_capital_source_payments.short_description = _(
        "Generate Capital Source Payments"
    )


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


@admin.register(models.CapitalSource)
class CapitalSourceAdmin(admin.ModelAdmin):
    """
    Admin view for :model:`lending.CapitalSource`
    """

    list_display = ("name", "source", "bank", "provider")

    def source(self, obj) -> str:
        return obj.get_source_display()


@admin.register(models.Loan)
class LoanAdmin(admin.ModelAdmin):
    """
    Admin view for :model:`lending.Loan`
    """

    actions = ["generate_amortization", "pre_terminate"]
    list_display = (
        "borrower",
        "loan_date",
        "amount_display",
        "interest_rate_display",
        "interest_amount",
        "interest_gained",
        "term",
        "next_payment_due_date",
        "payment_schedule",
        "remaining_payment_terms",
        "total_principal_receivables",
        "is_completed",
    )
    list_filter = (
        "borrower",
        "payment_schedule",
        "sources__capital_source__source",
        "borrower__is_borrower_active",
        "is_completed",
    )
    search_fields = ("borrower__first_name", "borrower__last_name")
    inlines = [LoanSourceAdminInline, AmortizationAdminInline]

    def amount_display(self, obj):
        amount = int(obj.amount) if obj.amount % 1 == 0 else obj.amount
        return intcomma(amount)

    amount_display.short_description = _("Amount")

    def interest_amount(self, obj):
        amount = (
            int(obj.interest_amount)
            if obj.interest_amount % 1 == 0
            else obj.interest_amount
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
            if obj.interest_gained % 1 == 0
            else obj.interest_gained
        )
        return intcomma(amount)

    def next_payment_due_date(self, obj):
        return obj.next_payment_due_date if obj.next_payment_due_date else "N/A"

    def remaining_payment_terms(self, obj):
        return obj.remaining_payment_terms

    def total_principal_receivables(self, obj):
        """
        Returns the total principal receivables of the loan.
        """
        amount = (
            int(obj.total_principal_receivables)
            if obj.total_principal_receivables % 1 == 0
            else obj.total_principal_receivables
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
                        amount_gained=(
                            loan.amortization_amount_due
                            - loan.sources.all().total_deductibles()
                        ),
                    )
                )

                if loan.is_payment_schedule_monthly:
                    due_date += relativedelta(months=1)
                else:
                    due_date += relativedelta(days=15)

            if amortization:
                models.Amortization.objects.bulk_create(amortization)

        messages.success(request, _("Successfully generated amortization."))

    generate_amortization.short_description = _("Generate Loan Amortization")

    def pre_terminate(self, request, queryset):
        """
        Pre-terminates the selected loans.
        """
        for loan in queryset:
            loan.pre_terminate()

        messages.success(request, _("Successfully pre-terminated selected loans."))

    pre_terminate.short_description = _("Pre-terminate selected Loans")
