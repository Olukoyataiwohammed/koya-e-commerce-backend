from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Message
from .serializers import MessageSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


# 📩 GET all messages + POST new message
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def message_list_create(request):
    if request.method == 'GET':
        messages = Message.objects.all().order_by('-created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 📩 GET single message (optional)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_detail(request, pk):
    try:
        message = Message.objects.get(pk=pk)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = MessageSerializer(message)
    return Response(serializer.data)