from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from .serializers import ToDoSerializer, ToDoCompleteSerializer
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.http import JsonResponse
from django.db import IntegrityError
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.models import User
from todo.models import Todo

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            data = JSONParser().parse(request)
            user = User.objects.create_user(data['username'], password=data['password'])
            user.save()
            token = Token.objects.create(user=user)
            return JsonResponse({'token': str(token)}, status=201)
        except IntegrityError:
            return JsonResponse({'error':'That username has already been taken. Please choose a new username'}, status=400)

@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        user = authenticate(request, username=data['username'], password=data['password'])
        if user is None:
            return JsonResponse({'error':'Could not login, please check username and password'}, status=400)
        else:
            try:
                token = Token.objects.get(user=user)
            except:
                token = Token.objects.create(user=user)
            return JsonResponse({'token': str(token)}, status=200)

class TodoCompletedList(generics.ListAPIView):
    serializer_class = ToDoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Todo.objects.filter(user=user, datecompleted__isnull=False).order_by('-datecompleted')
        
        
class TodoCreateList(generics.ListCreateAPIView):
    serializer_class = ToDoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Todo.objects.filter(user=user, datecompleted__isnull=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        
class TodoRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ToDoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        return Todo.objects.filter(user=user)
    
    def delete(self, request, *args, **kwargs):
        todo = Todo.objects.filter(pk=kwargs['pk'], user=self.request.user)
        if todo.exists():
            return self.destroy(request, *args, **kwargs)
        else:
            raise ValidationError('This is not your ToDo to delete, BRUH!')    
        
    
class TodoComplete(generics.UpdateAPIView):
    serializer_class = ToDoCompleteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        return Todo.objects.filter(user=user)
    
    def perform_update(self, serializer):
        serializer.instance.datecompleted = timezone.now()
        serializer.save()