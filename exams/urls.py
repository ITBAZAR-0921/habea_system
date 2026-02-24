from django.urls import path

from .views import (
    AttemptFinishView,
    AttemptQuestionView,
    ExamCreateView,
    ExamDeleteView,
    ExamListView,
    ExamQuestionManageView,
    ExamResultView,
    ExamStartView,
    ExamUpdateView,
)

urlpatterns = [
    path('', ExamListView.as_view(), name='exam_list'),
    path('manage/create/', ExamCreateView.as_view(), name='exam_create'),
    path('manage/<int:exam_id>/edit/', ExamUpdateView.as_view(), name='exam_update'),
    path('manage/<int:exam_id>/delete/', ExamDeleteView.as_view(), name='exam_delete'),
    path('manage/<int:exam_id>/questions/', ExamQuestionManageView.as_view(), name='exam_questions_manage'),
    path('<int:exam_id>/start/', ExamStartView.as_view(), name='exam_start'),
    path('attempt/<int:attempt_id>/question/<int:number>/', AttemptQuestionView.as_view(), name='attempt_question'),
    path('attempt/<int:attempt_id>/finish/', AttemptFinishView.as_view(), name='attempt_finish'),
    path('result/<int:attempt_id>/', ExamResultView.as_view(), name='exam_result'),
]
