from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.shortcuts import redirect
from .models import Link
from .serializers import LinkSerializer, LinkCreateSerializer

class LinkViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return LinkCreateSerializer
        return LinkSerializer

    @action(detail=False, methods=['post'])
    def shorten(self, request):
        """Create a new shortened link"""
        serializer = LinkCreateSerializer(data=request.data)
        if serializer.is_valid():
            link = Link.objects.create(original_url=serializer.validated_data['original_url'])
            return Response(LinkSerializer(link, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_all(self, request):
        """List all shortened links with pagination"""
        links = Link.objects.all().order_by('-created_at')
        page = self.paginate_queryset(links)
        if page is not None:
            serializer = LinkSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = LinkSerializer(links, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='redirect/(?P<short_code>[^/.]+)')
    def redirect_to_original(self, request, short_code=None):
        """Redirect from short code to original URL"""
        try:
            link = Link.objects.get(short_code=short_code)
            link.clicks += 1
            link.save()
            return redirect(link.original_url)
        except Link.DoesNotExist:
            raise NotFound("Short link not found")

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about all shortened links"""
        total_links = Link.objects.count()
        total_clicks = Link.objects.aggregate(total=models.Sum('clicks'))['total'] or 0
        return Response({
            'total_links': total_links,
            'total_clicks': total_clicks,
        })

from django.db import models
