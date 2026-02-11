
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from apps.loyalty.models import PointTransaction

@login_required
def transaction_report(request):
    """Reporte de transacciones de puntos por rango de fecha"""
    if not hasattr(request, 'tenant'):
        return redirect('users:login')
        
    # Filtros de fecha (por defecto: últimos 30 días)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.localtime() - timedelta(days=30)).date().isoformat()
    if not end_date:
        end_date = timezone.localtime().date().isoformat()
        
    transactions = PointTransaction.objects.filter(
        organization=request.tenant,
        created_at__date__range=[start_date, end_date]
    ).select_related('customer', 'performed_by').order_by('-created_at')
    
    # Totales del periodo
    total_earned = transactions.filter(transaction_type='EARN').aggregate(s=Sum('points'))['s'] or 0
    total_redeemed = transactions.filter(transaction_type='REDEEM').aggregate(s=Sum('points'))['s'] or 0
    
    context = {
        'transactions': transactions,
        'start_date': start_date,
        'end_date': end_date,
        'total_earned': total_earned,
        'total_redeemed': total_redeemed,
        'title': 'Reporte de Movimientos',
        'subtitle': f'Del {start_date} al {end_date}'
    }
    return render(request, 'reports/transaction_report.html', context)
