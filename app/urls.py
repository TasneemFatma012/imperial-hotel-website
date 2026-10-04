from django.urls import path
from app import views
urlpatterns = [
    path('',views.index,name="index"),
    path('about',views.about,name="about"),
    path('contact',views.contact,name="contact"),
    path('insert1',views.insert1Data,name="insert1data"),
    path('room',views.room,name="room") ,
    path('login',views.handlelogin,name="handlelogin"),
    path('signup',views.handlesignup,name="handlesignup"),
    path('logout',views.handlelogout,name="handlelogout"),
    path('insert',views.insertData,name="insertdata"),
    path('book',views.book,name="book"),
    path(
        'payment/<uuid:booking_token>/',
        views.payment,
        name="payment",
    ),
    path(
        'payment/<uuid:booking_token>/verify/',
        views.verify_payment,
        name="verify_payment",
    ),
    path('service',views.service,name="service"),
    path('standard',views.standard,name="standard"),
    path('standardbook',views.standardbook,name="standardbook"),

    path('deluxe',views.deluxe,name="deluxe"),
    path('deluxebook',views.deluxebook,name="deluxebook"),
    path('imperial',views.imperial,name="imperial"),
    path('imperialbook',views.imperialbook,name="imperialbook"),
    path('faq',views.faq,name="faq"),
    # path('payment',views.payment,name="payment"),
    path("insert3",views.insert3Data,name="insert3data"),
    path("insert4",views.insert4Data,name="insert4data"),
    path("insert5",views.insert5Data,name="insert5data"),




]
