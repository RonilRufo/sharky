import datetime
import math
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models
from django.db.models import Case, DecimalField, F, Q, Sum, Value, When
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils.models import TimeStampedModel

from sharky.mixins import UUIDPrimaryKeyMixin


class Bank(UUIDPrimaryKeyMixin):
    """
    Stores information about a bank.
    """

    name = models.CharField(max_length=128, unique=True)
    abbreviation = models.CharField(max_length=32, blank=True)

    class Meta:
        verbose_name = _("Bank")
        verbose_name_plural = _("Banks")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.abbreviation})" if self.abbreviation else self.name


class CapitalSource(UUIDPrimaryKeyMixin, TimeStampedModel):
    """
    Stores information about the source of the capital money(where the money used for
    capital came from).
    """

    SOURCES = Choices(
        ("savings", _("Savings Account")),
        ("credit_card", _("Credit Card")),
        ("loan", _("Cash Loan")),
    )

    source = models.CharField(max_length=32, choices=SOURCES)
    bank = models.ForeignKey(
        "lending.Bank",
        related_name="capital_sources",
        on_delete=models.CASCADE,
        help_text=_("The bank in which the capital money came from."),
    )
    name = models.CharField(
        max_length=64,
        help_text=_("Reference name of the source account."),
    )
    from_third_party = models.BooleanField(
        default=False,
        help_text=_(
            "If the capital source came from another person other than the owner."
        ),
    )
    provider = models.ForeignKey(
        get_user_model(),
        related_name="capital_sources",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=_(
            "The third-party provider of the capital source other than the owner. If "
            "the provider is the owner, leave this blank."
        ),
    )

    class Meta:
        verbose_name = _("Capital Source")
        verbose_name_plural = _("Capital Sources")
        ordering = ("-created",)

    def __str__(self) -> str:
        return self.name

    @property
    def is_savings(self) -> bool:
        """
        Returns whether the source is from the savings account or not.
        """
        return self.source == self.SOURCES.savings


class LoanSourceQuerySet(models.QuerySet):
    """
    Custom queryset for :model:`lending.LoanSource`
    """

    def total_amount_earned(self):
        """
        Returns the total amount earned from the selected loan sources.
        """
        amount = self.annotate(
            amount_gained=Case(
                When(
                    capital_source__source=CapitalSource.SOURCES.savings,
                    capital_source__provider__isnull=True,
                    then=F("amount") * (F("loan__interest_rate") / 100),
                ),
                When(
                    ~Q(capital_source__source=CapitalSource.SOURCES.savings),
                    then=(
                        F("amount")
                        * ((F("loan__interest_rate") - F("interest_rate")) / 100)
                    ),
                ),
                default=Value(0),
                output_field=DecimalField(),
            )
        ).aggregate(total=Sum("amount_gained"))
        return math.floor(amount["total"]) if amount["total"] else 0


class Loan(UUIDPrimaryKeyMixin, TimeStampedModel):
    """
    Stores main information about a loan made.
    """

    PAYMENT_SCHEDULES = Choices(
        ("monthly", _("Monthly")),
        ("bi_monthly", _("Bi-monthly")),
    )
    borrower = models.ForeignKey(
        get_user_model(),
        related_name="loans",
        on_delete=models.CASCADE,
        null=True,
    )
    borrower_name = models.CharField(
        max_length=128,
        blank=True,
        help_text=_("Name of the actual borrower if known."),
    )
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term = models.PositiveSmallIntegerField(help_text=_("Term duration in months."))
    payment_schedule = models.CharField(
        max_length=32,
        choices=PAYMENT_SCHEDULES,
        default=PAYMENT_SCHEDULES.monthly,
    )
    first_payment_date = models.DateField(default=timezone.now)
    is_completed = models.BooleanField(default=False)
    loan_date = models.DateField()

    class Meta:
        verbose_name = _("Loan")
        verbose_name_plural = _("Loans")
        ordering = ("-loan_date",)

    def __str__(self) -> str:
        amount = intcomma(self.amount)
        return f"{self.borrower} | {amount} | {self.loan_date}"

    @property
    def amortization_amount_due(self) -> Decimal:
        """
        The amount due for each amortization for this loan.
        """
        amortization_count = (
            self.term if self.is_payment_schedule_monthly else self.term * 2
        )
        principal = self.amount / amortization_count
        interest = (
            self.interest_amount
            if self.is_payment_schedule_monthly
            else self.interest_amount / 2
        )
        total = principal + interest
        return round(total, 2)

    @property
    def payments_made(self) -> str:
        """
        Returns the number of amortizations paid over the duration of the term.
        """
        made = self.amortizations.filter(paid_date__isnull=False).count()
        return f"{made} out of {self.term}"

    @property
    def next_payment_due_date(self) -> datetime.date:
        """
        Returns the next payment due date based on the unpaid amortization.
        """
        amortization = self.amortizations.filter(paid_date__isnull=True).first()
        return amortization.due_date if amortization else None

    @property
    def is_payment_schedule_monthly(self) -> bool:
        """
        Returns whether the payment schedule is monthly or not.
        """
        return self.payment_schedule == self.PAYMENT_SCHEDULES.monthly

    @property
    def principal_amount(self) -> Decimal:
        """
        Returns the principal amount with respect to the term duration.
        """
        amount = self.amount / self.term
        return round(amount, 2)

    @property
    def interest_amount(self) -> Decimal:
        """
        The amount gained from the interest rate of the loan.
        """
        income = self.amount * (self.interest_rate / 100)
        return round(income, 2)

    @property
    def total_interest(self) -> Decimal:
        """
        Returns the total amount gained from the interest rate of the loan when all
        payments are made.
        """
        total = self.interest_amount * self.term
        return round(total, 2)

    @property
    def total_amount(self) -> Decimal:
        """
        The sum of the principal amount and all interests gained within the term.
        """
        total = self.interest_amount + self.total_interest
        return round(total, 2)

    @property
    def interest_gained(self) -> Decimal:
        """
        Returns the total interest gained depending on the sources of the loan.
        """
        gained_amount = self.sources.all().total_amount_earned()
        return round(gained_amount, 2)

    @property
    def total_interest_gained(self) -> Decimal:
        """
        Returns the total interest gained with respect to the sources and the term
        duration.
        """
        total = self.interest_gained * self.term
        return round(total, 2)

    @property
    def remaining_payment_terms(self) -> int:
        """
        Returns the remaining payment terms until all payments for the loan is
        completed. This is equivalent to the number of unpaid amortizations for the
        loan.
        """
        return self.amortizations.filter(paid_date__isnull=True).count()

    @property
    def total_principal_receivables(self) -> Decimal:
        """
        Returns the total principal receivables for the selected loan. This will only
        apply to loans having savings account as their source.
        """
        amount = 0
        sources = self.sources.filter(
            capital_source__source=CapitalSource.SOURCES.savings,
            capital_source__provider__isnull=True,
        )
        if sources.exists():
            receivable = sources.annotate(
                receivables=F("amount") / F("loan__term")
            ).aggregate(total=Sum("receivables"))
            amount = receivable["total"] * self.remaining_payment_terms

        if not self.is_payment_schedule_monthly:
            amount /= 2

        return math.floor(amount)

    def pre_terminate(self) -> None:
        """
        Terminates the loan before completing all amortizations. As a general rule, all
        remaining amortization will be calculated again using a 1% interest rate. The
        following formula will be used to recalculate amortization amount:

        (loan amount * (1 / 100)) + (loan amount / term)

        The value will be assigned to all remaining amortization of the loan.
        """
        value = (self.amount * Decimal("0.01")) + self.principal_amount
        self.amortizations.filter(paid_date__isnull=True).update(
            amount_due=value,
            paid_date=timezone.now(),
            is_preterminated=True,
        )
        self.is_completed = True
        self.save(update_fields=["is_completed"])


class LoanSource(UUIDPrimaryKeyMixin, TimeStampedModel):
    """
    Stores further information about the source of the capital money used in a loan.
    """

    loan = models.ForeignKey(
        "lending.Loan",
        related_name="sources",
        on_delete=models.CASCADE,
    )
    capital_source = models.ForeignKey(
        "lending.CapitalSource",
        related_name="loan_sources",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_(
            "The interest rate from the bank if the source came from credit card or "
            "cash loan."
        ),
    )
    monthly_amortization = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Only applicable if the source comes from any other than savings."),
    )
    loan_applied_date = models.DateField(
        blank=True,
        null=True,
        help_text=_("The date when the loan was applied to in the bank."),
    )
    loan_received_date = models.DateField(
        blank=True,
        null=True,
        help_text=_(
            "The date when the loan from the credit card or cash loan was received."
        ),
    )

    objects = LoanSourceQuerySet.as_manager()

    class Meta:
        verbose_name = _("Loan Source")
        verbose_name_plural = _("Loan Sources")
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"{self.loan} -> {self.capital_source}"

    @property
    def interest_amount(self) -> Decimal:
        """
        The amount gained from the interest rate of the selected source. This will only
        apply to credit cards and cash loans. If the source comes from a savings
        account, this will return 0.
        """
        if self.capital_source.is_savings:
            return 0

        income = self.loan.amount * (self.interest_rate / 100)
        return round(income, 2)


class LoanSourceAmortization(UUIDPrimaryKeyMixin):
    """
    The monthly amortization for a certain loan source if the source came from any other
    than the savings type. This will be mainly used to track down amortization for a
    certain loan made by the owner to a certain bank.
    """

    source = models.ForeignKey(
        "lending.LoanSource",
        related_name="amortizations",
        on_delete=models.CASCADE,
    )
    due_date = models.DateField()
    paid_date = models.DateField(blank=True, null=True)
    amount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        help_text=_("The monthly amortization amount due."),
    )
    is_preterminated = models.BooleanField(blank=False)
    pretermindated_interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text=_(
            "The interest rate provided by the bank in the case ofpre-termination of "
            "the loan."
        ),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Loan Source Amortization")
        verbose_name_plural = _("Loan Source Amortizations")
        ordering = ("due_date",)

    def __str__(self):
        return f"{self.source.capital_source.name}: {self.amount} on {self.due_date}"


class Amortization(UUIDPrimaryKeyMixin, TimeStampedModel):
    """
    The amortization to be paid by the borrower depending on the payment schedule.
    """

    AMORTIZATION_TYPES = Choices(
        ("full_payment", _("Full Payment")),
        ("interest_only", _("Interest Only")),
        ("principal_only", _("Principal Only")),
    )
    loan = models.ForeignKey(
        "lending.Loan",
        related_name="amortizations",
        on_delete=models.CASCADE,
    )
    amount_due = models.DecimalField(max_digits=9, decimal_places=2)
    amort_type = models.CharField(
        _("Amortization Type"),
        max_length=32,
        choices=AMORTIZATION_TYPES,
        default=AMORTIZATION_TYPES.full_payment,
    )
    due_date = models.DateField()
    paid_date = models.DateField(blank=True, null=True)
    is_preterminated = models.BooleanField(default=False)
    amount_gained = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        help_text=_(
            "Also referred to as the income for this particular loan on a monthly "
            "basis."
        ),
    )

    class Meta:
        verbose_name = _("Amortization")
        verbose_name_plural = _("Amortization")
        ordering = ("due_date",)

    def __str__(self) -> str:
        amount_due = intcomma(self.amount_due)
        return f"{self.loan.borrower} | {amount_due} | {self.due_date}"

    @property
    def payment_stage(self) -> str:
        """
        Returns information on what stage is the current amortization on.
        """
        current = self.loan.amortizations.filter(due_date__lt=self.due_date).count() + 1
        count = self.loan.amortizations.all().count()
        return f"{current} of {count}"
