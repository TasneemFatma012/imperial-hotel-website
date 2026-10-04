from django.db import models
from django.db.models import F, Q
from django.utils import timezone
import uuid


class Contact1(models.Model):
    name1=models.CharField(max_length=25,blank=False,null=False)   
    emaild=models.EmailField() 
    msg=models.CharField(max_length=2000,blank=False,null=False)   
class reservation3(models.Model):
    name=models.CharField(max_length=25,blank=False,null=False)
    emails=models.EmailField()
    type1=models.CharField(max_length=25,blank=False,null=False)
    
    guest=models.CharField(max_length=25,blank=False,null=False)
    checkin=models.DateField(auto_now=True, auto_now_add=False)
    gridRadios=models.CharField(max_length=25,blank=False,null=False)
    comment=models.CharField(max_length=25,blank=False,null=False)

class reservation2(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Payment pending"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Payment failed"
        REFUND_PENDING = "refund_pending", "Refund pending"
        REFUNDED = "refunded", "Refunded"

    fname=models.CharField(max_length=25)  
    lname=models.CharField(max_length=25)  
    phone=models.CharField(max_length=20)
    email=models.EmailField()
    room=models.CharField(max_length=25,blank=False,null=False)  
    date=models.DateField()
    checkout_date=models.DateField(null=True, blank=True)
    amount_paise=models.PositiveIntegerField(default=0)
    payment_order_id=models.CharField(max_length=64, blank=True)
    payment_id=models.CharField(max_length=64, blank=True)
    checkout_token=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status=models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    created_at=models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(checkout_date__isnull=True) | Q(checkout_date__gt=F("date")),
                name="reservation_checkout_after_arrival",
            )
        ]



# Create your models here.
