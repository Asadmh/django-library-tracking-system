from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, MemberSerializer, LoanSerializer, ExtendDueDateSerializer
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Count, Q
from .tasks import send_loan_notification
from .pagination import BooksResultsSetPagination

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().select_related('author')
    serializer_class = BookSerializer
    pagination_class = BooksResultsSetPagination

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan = Loan.objects.create(book=book, member=member)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    @action(detail=False, methods=['get'])
    def top_active(self, request, pk=None):
        # members = self.get_queryset().annotate('active_loans'=Count('loans', filter=Q(loans__is_returned=False))).order_by('active_loans'))[:5]
        #

        # data = []
        # for member in members:
        #     data.append({
        #         "id": member.id
        #     })
        #

        # #uncomplete due to time restriction
        pass


class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=True, methods=['post'])
    def extend_due_date(self, request, pk=None):
        loan = self.get_object()
        try:
            serializer = ExtendDueDateSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)

            additional_days = serializer.validated_data['additional_days']
            success = loan.extend_overdue_date(additional_days)
            if success:
                return Response(status=status.HTTP_200_OK, data=f"Loan has been successfully extended by {additional_days} days")

            return Response(status=status.HTTP_400_BAD_REQUEST, data="Due date has passed")

        except Exception as err:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=err)
