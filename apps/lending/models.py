from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils.models import TimeStampedModel

from sharky.mixins import UUIDPrimaryKeyMixin


class Bank(UUIDPrimaryKeyMixin):
    """
    Stores information about a bank.
    """
    name = models.CharField(max_length=128)
    abbreviation = models.CharField(max_length=32, blank=True)

    class Meta:
        verbose_name = _("Bank")
        verbose_name_plural = _("Banks")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.abbreviation})" if self.abbreviation else self.name


class Borrower(UUIDPrimaryKeyMixin, TimeStampedModel):
    """
    The borrower of the loan.
    """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    class Meta:
        verbose_name = _("Borrower")
        verbose_name_plural = _("Borrowers")
        ordering = ("last_name", "first_name")

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


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

    class Meta:
        verbose_name = _("Capital Source")
        verbose_name_plural = _("Capital Sources")
        ordering = ("-created",)

    def __str__(self) -> str:
        return self.name


class Loan(UUIDPrimaryKeyMixin, TimeStampedModel):
    """
    Stores main information about a loan made.
    """
    PAYMENT_SCHEDULES = Choices(
        ("monthly", _("Monthly")),
        ("bi_monthly", _("Bi-monthly")),
    )
    borrower = models.ForeignKey(
        "lending.Borrower",
        related_name="loans",
        on_delete=models.CASCADE,
    )
    borrower_name = models.CharField(
        max_length=128,
        blank=True,
        help_text=_("Name of the actual borrower if known."),
    )
    amount = models.DecimalField(max_digits=9,decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term = models.PositiveSmallIntegerField(help_text=_("Term duration in months."))
    payment_schedule = models.CharField(
        max_length=32,
        choices=PAYMENT_SCHEDULES,
        default=PAYMENT_SCHEDULES.monthly,
    )
    day_deadline = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(31)],
        help_text=_("The day of the month in which the due date will fall."),
    )
    is_completed = models.BooleanField(default=False)
    loan_date = models.DateField()

    class Meta:
        verbose_name = _("Loan")
        verbose_name_plural = _("Loans")
        ordering = ("-loan_date",)

    def __str__(self) -> str:
        amount = intcomma(self.amount)
        return f"{self.borrower} | {amount} | {self.loan_date}"


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
        help_text=_(
            "The interest rate from the bank if the source came from credit card or "
            "cash loan."
        ),
    )
    day_deadline = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_(
            "The day of the month that the due date usually falls if the source came "
            "from credit card or cash loan."
        ),
    )
    term = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text=_(
            "The term duration of the loan if the source is credit card or cash loan."
        ),
    )
    loan_received_date = models.DateField(
        blank=True,
        null=True,
        help_text=_(
            "The date when the loan from the credit card or cash loan was received."
        ),
    )

    class Meta:
        verbose_name = _("Loan Source")
        verbose_name_plural = _("Loan Sources")
        ordering = ("-created", )

    def __str__(self) -> str:
        return f"{self.loan} -> {self.capital_source}"


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

    class Meta:
        verbose_name = _("Amortization")
        verbose_name_plural = _("Amortization")
        ordering = ("due_date",)

    def __str__(self) -> str:
        amount_due = intcomma(self.amount_due)
        return f"{self.loan.borrower} | {amount_due} | {self.due_date}"
