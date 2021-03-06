from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import MyUser, MyGroup, Task, Feedback, Meeting
from .permissions import IsAdminUser, IsTeacherAndLoggedIn
from .serializers import UserSerializer, GroupSerializer, TaskSerializer, FeedbackSerializer, MeetingSerializer
import json


# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    queryset = MyUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        permission_classes = []
        if self.action == 'create':
            # permission_classes = [AllowAny]
            permission_classes = [IsAdminUser]
        elif self.action == 'retrieve' or self.action == 'update' or self.action == 'partial_update':
            permission_classes = [AllowAny]
            # permission_classes = [IsLoggedInUserOrAdmin]
        elif self.action == 'list' or self.action == 'destroy':
            # permission_classes = [IsAdminUser]
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = MyGroup.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated, IsTeacherAndLoggedIn)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_permissions(self):
        permission_classes = []
        if self.action == 'create':
            permission_classes = [IsAdminUser]
        elif self.action == 'update' or self.action == 'partial_update' or self.action == 'destroy':
            permission_classes = [IsAdminUser]
        elif self.action == 'retrieve' or self.action == 'list':
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = (IsAuthenticated, IsTeacherAndLoggedIn)


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = (IsAuthenticated, IsTeacherAndLoggedIn)


@api_view(['GET'])
def get_loggedin_user_details(request):
    user = {
        'id': request.user.id,
        'email': request.user.email,
        'is_student': request.user.is_student,
        'groupId': request.user.groupId.id,
        'availability': request.user.availability,
    }
    return JsonResponse(user, safe=False)


@api_view(['GET'])
def group_details_of_user(request, user_id):
    user = MyUser.objects.get(id=user_id)
    group_id = user.groupId.id
    group = MyGroup.objects.get(id=group_id)
    group_body = {
        'id': group.id,
        'name': group.name
    }
    return JsonResponse(group_body, safe=False)


@api_view(['GET'])
def feedbacks_of_user(request, user_id):
    if request.user.id == user_id:
        user = MyUser.objects.get(id=user_id)
        feedbacks = list(Feedback.objects.filter(receiverId=user).values())
        return JsonResponse(feedbacks, safe=False)
    else:
        if request.user.is_student:
            return HttpResponse("You can't access this info")
        else:
            user = MyUser.objects.get(id=user_id)
            feedbacks = list(Feedback.objects.filter(receiverId=user).values())
            return JsonResponse(feedbacks, safe=False)


@api_view(['GET'])
def users_of_group(request, group_id):
    group = MyGroup.objects.get(id=group_id)
    users = list(MyUser.objects.filter(groupId=group).values("id", "email", "is_student", "availability"))
    return JsonResponse(users, safe=False)


@api_view(['GET'])
def meetings_of_group(request, group_id):
    group = MyGroup.objects.get(id=group_id)
    meetings = list(Meeting.objects.filter(groupId=group).values())
    return JsonResponse(meetings, safe=False)


@api_view(['POST'])
def set_user_availability(request, user_id):
    if request.user.is_student:
        body = json.loads(request.body)
        user = MyUser.objects.get(id=user_id)
        user.availability = str(body['start']) + '-' + str(body['end'])
        updated_user = {
            'id': user.id,
            'email': user.email,
            'is_student': user.is_student,
            'groupId': user.groupId.id,
            'availability': user.availability
        }
        return JsonResponse(updated_user, safe=False)


@api_view(['GET'])
def meetings_of_user(request, user_id):
    user = MyUser.objects.get(id=user_id)
    meetings = list(Meeting.objects.filter(groupId=user.groupId.id).values())
    return JsonResponse(meetings, safe=False)


@api_view(['POST'])
def set_meeting(request, group_id):
    # meeting_duration 1hr and meeting_window <= 3*meeting_duration
    if not request.user.is_student:
        body = json.loads(request.body)
        n = len(body['start'])

        for i in range(0, n):
            body['end'][i] -= 100

        maxa = max(body['start'])
        maxb = max(body['end'])
        maxc = max(maxa, maxb)
        x = (maxc + 2) * [0]
        cur = 0
        idx = 0

        for i in range(0, n):
            x[body['start'][i]] += 1
            x[body['end'][i] + 1] -= 1

        maxy = -1

        for i in range(0, maxc + 1):
            cur += x[i]
            if maxy < cur:
                maxy = cur
                idx = i

        meeting_start_time = idx
        meeting_end_time = idx + 100 if idx < 2400 else 0000
        users_in_group = list(MyUser.objects.filter(groupId=int(group_id)).values("id"))
        meeting = {
            'groupId': int(group_id),
            'user': users_in_group,
            'url': 'some-zoom-link',
            'time': str(meeting_start_time) + ':' + str(meeting_end_time)
        }
        return JsonResponse(meeting, safe=False)
