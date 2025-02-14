from django.shortcuts import render,redirect
from django.db.models import Q
from django.http import HttpResponse
from .models import Room,Topic,Message,User
from .forms import RoomForm, UserForm,MyUserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout 
from django.contrib.auth.decorators import login_required

# Create your views here.

def loginPage(request):

    page = 'login'

    # check if the user is authenticated or not 
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        if email and password:  # Check if both fields are provided
            # check if user exist or not 
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'User does not exist')
            
            user = authenticate(request,email=email,password=password)

            if user is not None:
                login(request,user)
                return redirect('home')
            else:
                messages.error(request,'Email OR password does not exist')
        else:
            messages.error(request, 'Both email and password are required')

    context = {'page':page}
    return render(request,'base/login_register.html',context)


def logoutUser(request):
    logout(request)
    return redirect('home')



def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,"An error occured during registration")

    return render(request,'base/login_register.html',{'forms':form})



def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        )
    topics = Topic.objects.all()[0:6]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms':rooms,'topics':topics,'room_count':room_count,'room_messages':room_messages}
    return render(request,'base/home.html',context)



def room(request,pk): 
    room = Room.objects.get(id=pk)
    # way to retreive all the messages
    room_messages = room.message_set.all()
    participants = room.participants.all()


    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)     # when user will do the comment the it will be add to the participants
        return redirect('room',pk=room.id)
    context = {'room':room,'room_messages':room_messages,'participants':participants}
    return render(request,'base/room.html',context)


def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user':user,'rooms':rooms,'room_messages':room_messages,'topics':topics}
    return render(request,'base/profile.html',context)





@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        # here if the topic not exist then the new topic will created
        topic,created = Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')
    
    context = {'form':form,'topics':topics}
    return render(request,'base/room_form.html',context)




@login_required(login_url='login')
def updateRoom(request,pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()


    # only the host user allowed to update
    if request.user != room.host:
        return HttpResponse("You are not allowed to change!!")

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic,created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')        
        room.topic = topic        
        room.description = request.POST.get('description')        
        room.save()
        return redirect('home')
    context = {'form':form,'topics':topics,'room':room}
    return render(request,'base/room_form.html',context)


@login_required(login_url='login')
def deleteRoom(request,pk):
    room = Room.objects.get(id=pk)

    # only the host user allowed to delete
    if request.user != room.host:
        return HttpResponse("You are not allowed to delete!!")

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj':room})



# 
@login_required(login_url='login')
def deleteMessge(request,pk):
    message = Message.objects.get(id=pk)

    # only the host user allowed to delete
    if request.user != message.user:
        return HttpResponse("You are not allowed to delete this message!!")

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj':message})



@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST,instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile',pk=user.id)
    return render(request,'base/update_user.html',{'form':form})



def topicPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics':topics}
    return render(request,'base/topic.html',context)



def activityPage(request):
    room_message = Message.objects.all()
    context = {'room_messages':room_message}
    return render(request,'base/activity.html',context)
