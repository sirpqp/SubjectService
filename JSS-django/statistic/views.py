from datetime import datetime
from django.db import connection
from collections import namedtuple
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from django_filters import rest_framework as myfilter
from statistic.serializers import *
from rest_framework.pagination import PageNumberPagination
from .models import *
import json
from .old import old_data


class UnlimitedPagination(PageNumberPagination):
    page_size = None
    page_size_query_param = 'page_size'
    max_page_size = None


sql_base = '''
    with a as (
        select 
            date_registered,
            data_replied,
            api_task.status,
            api_restype.name res_type,
            api_resource.lang lang,
            api_customer.nickname custom,api_customer.dept,
            api_group.id,api_group.name,api_group.organ_id,
            api_organ.name oname,
            reg.id reg_id,reg.nickname reg_name,
            reply.id reply_id,reply.nickname reply_name,
            [count]
        from api_task
        left join api_request on api_request.id=api_task.request_id 
        left join api_customer on api_customer.id=api_request.customer_id
        left join api_resource on api_resource.id=api_task.resource_id
        left join api_user reply on reply.id=api_task.replier_id
        left join api_user reg on reg.id=api_request.registrar_id
        left join api_restype on api_resource.restype_id=api_restype.id
        left join api_group on api_request.group_id=api_group.id
        left join api_organ on api_organ.id=api_group.organ_id
    )
    '''
sql_data = '''
    with a as (
        select 
            date_registered,
            data_replied,
            api_task.status,
            api_restype.name res_type,
            api_resource.lang lang,
            api_customer.nickname custom,api_customer.dept,
            api_group.id gid,api_group.name,api_group.organ_id,
            api_organ.name oname,
            reg.id reg_id,reg.nickname reg_name,
            reply.id reply_id,reply.nickname reply_name,
            [count]
        from api_task
        left join api_request on api_request.id=api_task.request_id 
        left join api_customer on api_customer.id=api_request.customer_id
        left join api_resource on api_resource.id=api_task.resource_id
        left join api_user reply on reply.id=api_task.replier_id
        left join api_user reg on reg.id=api_request.registrar_id
        left join api_restype on api_resource.restype_id=api_restype.id
        left join api_group on api_request.group_id=api_group.id
        left join api_organ on api_organ.id=api_group.organ_id
        where date_registered between %s and DATEADD(day,1,%s)
    )
    '''


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    客服工作情况统计表
    """
    serializer_class = UserSerializer
    pagination_class = UnlimitedPagination

    def get_queryset(self):
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        gid = self.request.query_params.get('gid', None)
        where = f'gid={gid}' if gid is not None else '1=1'
        sql = f'''
            select 
                ROW_NUMBER() over(order by reply_id) id,
                reply_name name,
                SUM(case status when 'success' then [count] end) total
            from a
            where reply_id in (3,4,5,6,7,8,32,33) and {where}
            group by reply_id,reply_name
            '''
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        queryset = User.objects.raw(sql_data + sql, [begin, end])
        return queryset


class TotalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    服务情况总表
    """
    serializer_class = TotalSerializer
    pagination_class = UnlimitedPagination

    def get_queryset(self):
        gid = self.request.query_params.get('gid', None)
        where = f'gid={gid}' if gid is not None else '1=1'
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        sql = f'''
            select 
                ROW_NUMBER() over(order by CONVERT(varchar(10),date_registered,111)) id,
                CONVERT(varchar(10),date_registered,111) date,
                SUM([count])total,
                SUM(case status when 'success' then [count] end)success
            from a
            where {where}
            group by CONVERT(varchar(10),date_registered,111)
            '''

        queryset = Total.objects.raw(sql_data + sql, [begin, end])
        return queryset


class D1ViewSet(viewsets.ReadOnlyModelViewSet):
    """
    服务情况统计表D1 今日服务量
    """
    sql = '''
        select 
            ROW_NUMBER() over(order by SUM([count])) id,
            SUM([count]) total,
            (select SUM([count]) from a where DATEDIFF(day,date_registered,getdate())=0) today,
            (select SUM([count]) from a where DATEDIFF(day,date_registered,getdate()-1)=0) yesterday,
            (select SUM([count]) from a where DATEDIFF(day,date_registered,getdate()-7)=0) week,
            (select count(distinct CONVERT(varchar(10),date_registered,111)) from a) days,
            (select MAX(total) from (select SUM([count])total from a where DATEDIFF(MONTH,date_registered,getdate())=0 group by CONVERT(varchar(10),date_registered,111))b) max
        from a
        '''
    queryset = D1.objects.raw(sql_base + sql)
    serializer_class = D1Serializer
    pagination_class = UnlimitedPagination


class D2ViewSet(viewsets.ReadOnlyModelViewSet):
    """
    服务情况统计表D2 分时需求量
    """
    sql = '''
        select 
            ROW_NUMBER() over(order by CONVERT(varchar(10),date_registered,111)) id,
            CONVERT(varchar(10),date_registered,111) date,
            DATEPART(HOUR,date_registered) hour,
            SUM([count]) total
        from a
        where DATEDIFF(day,date_registered,getdate())=0
        group by CONVERT(varchar(10),date_registered,111),DATEPART(HOUR,date_registered)
        order by CONVERT(varchar(10),date_registered,111),DATEPART(HOUR,date_registered)
        '''
    queryset = D2.objects.raw(sql_base + sql)
    serializer_class = D2Serializer
    pagination_class = UnlimitedPagination


class D3ViewSet(viewsets.ReadOnlyModelViewSet):
    """
    服务情况统计表D3 总服务量
    """
    sql = '''
        select 
            ROW_NUMBER() over(order by CONVERT(varchar(10),date_registered,111)) id,
            CONVERT(varchar(10),date_registered,111) date,
            SUM([count]) total
        from a
        where DATEDIFF(day,date_registered,getdate())<30
        group by CONVERT(varchar(10),date_registered,111)
        order by CONVERT(varchar(10),date_registered,111)
        '''
    queryset = D3.objects.raw(sql_base + sql)
    serializer_class = D3Serializer
    pagination_class = UnlimitedPagination


class D4ViewSet(viewsets.ReadOnlyModelViewSet):
    """
    服务情况统计表D4 成功回复率
    """
    sql = '''
        select 
            ROW_NUMBER() over(order by SUM([count])) id,
            SUM([count]) total,
            (select SUM([count]) from a where DATEDIFF(day,date_registered,getdate())=0 and status='success') today,
            (select SUM([count]) from a where DATEDIFF(day,date_registered,getdate()-1)=0 and status='success') yesterday,
            (select SUM([count]) from a where DATEDIFF(day,date_registered,getdate()-7)=0 and status='success') week
        from a
        where status='success'
        '''
    queryset = D4.objects.raw(sql_base + sql)
    serializer_class = D4Serializer
    pagination_class = UnlimitedPagination


class CustomViewSet(viewsets.ReadOnlyModelViewSet):
    """
    客户日活情况
    """
    sql = '''
        select 
            ROW_NUMBER() over(order by date) id,
            b.date,
            SUM([count]) total
        from (
            select top 100 percent
                CONVERT(varchar(10),date_registered,111)date,
                custom
            from a 
            group by CONVERT(varchar(10),date_registered,111),custom
            order by CONVERT(varchar(10),date_registered,111)
            )b
        group by date
        '''
    queryset = Custom.objects.raw(sql_base + sql)
    serializer_class = CustomSerializer
    pagination_class = UnlimitedPagination


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    客户日活情况
    """
    sql = '''
        select 
            ROW_NUMBER() over(order by SUM([count]) desc) id,
            name,
            SUM([count]) total
        from a
        group by name
        '''
    queryset = Group.objects.raw(sql_base + sql)
    serializer_class = GroupSerializer
    pagination_class = UnlimitedPagination


class ResViewSet(viewsets.ReadOnlyModelViewSet):
    """
    资源类型占比
    """
    sql = '''
        select
            ROW_NUMBER() over(order by SUM([count]) desc) id,
            res_type,
            SUM([count]) total
        from a
        where res_type is not NULL
        group by res_type
        '''
    queryset = Res.objects.raw(sql_base + sql)
    serializer_class = ResSerializer
    pagination_class = UnlimitedPagination


class OrganViewSet(viewsets.ReadOnlyModelViewSet):
    """
    机构排名。
    """
    serializer_class = OrganSerializer
    pagination_class = UnlimitedPagination

    def get_queryset(self):
        sql = '''
            select 
                organ_id id,
                oname name,
                SUM([count]) total,
                SUM(case a.status when 'success' then [count] else 0 end) success,
                SUM(case a.status when 'failed' then [count] else 0 end) failed
            from a
            where oname like %s
            group by organ_id,oname
            order by SUM([count]) desc
            '''
        name = self.request.query_params.get('name', '')
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        queryset = Organ.objects.raw(sql_data + sql,
                                     [begin, end, '%' + name + '%'])
        # 不限时间时，加上旧数据
        if begin == '1970-01-01':
            for x in queryset:
                for y in old_data:
                    if x.id == y['id']:
                        x.total += y['total']
                        x.success += y['success']
                        x.failed += y['failed']
        return queryset


class DeptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeptSerializer
    pagination_class = UnlimitedPagination

    def get_queryset(self):
        sql = '''
        select 
            ROW_NUMBER() over(order by SUM([count]) desc) id,
            dept type,
            SUM([count]) value
        from a
        where organ_id=%s
        group by dept
        '''
        oid = self.request.query_params.get('oid')
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        queryset = Dept.objects.raw(sql_data + sql, [begin, end, oid])
        return queryset


class SuccessViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SuccessSerializer
    pagination_class = UnlimitedPagination

    def get_queryset(self):
        sql = '''
        select top 1
            %s id,
            ROUND((select SUM([count]) from a where organ_id=%s and status='success')*100/(select SUM([count]) from a where organ_id=%s),0)success,
            ROUND((select SUM([count])*100/(select SUM([count]) from a where organ_id=%s) from a where organ_id=%s and status!='success'),0)failed
        '''
        oid = self.request.query_params.get('oid')
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        queryset = Success.objects.raw(sql_data + sql,
                                       [begin, end, oid, oid, oid, oid, oid])
        return queryset


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LanguageSerializer
    pagination_class = UnlimitedPagination

    def get_queryset(self):
        sql = '''
        select top 1
            %s id,
            (select SUM([count]) from a where organ_id=%s and lang='ZH')ZH,
	        (select SUM([count]) from a where organ_id=%s and lang='F')F
        '''
        oid = self.request.query_params.get('oid')
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        queryset = Success.objects.raw(sql_data + sql,
                                       [begin, end, oid, oid, oid])
        return queryset


class TypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TypeSerializer
    pagination_class = UnlimitedPagination

    def get_queryset(self):
        sql = '''
        select 
            ROW_NUMBER() over(order by SUM([count]) desc) id,
            (case when res_type is null then '不明' else res_type end) type,
            SUM([count])sales 
        from a
        where organ_id=%s
        group by res_type
        '''
        oid = self.request.query_params.get('oid')
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        queryset = Type.objects.raw(sql_data + sql, [begin, end, oid])
        return queryset


class ReportCustomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReportCustomSerializer
    pagination_class = UnlimitedPagination

    def get_queryset(self):
        sql = '''
        select 
            ROW_NUMBER() over(order by SUM([count]) desc) id,
            custom name,
            (case when dept is null then '不明' else dept end)dept,
            SUM([count])total from a
        where organ_id=%s
        group by custom,dept
        '''
        oid = self.request.query_params.get('oid')
        begin = self.request.query_params.get('begin', '1970-01-01')
        end = self.request.query_params.get('end', datetime.now())
        queryset = ReportCustom.objects.raw(sql_data + sql, [begin, end, oid])
        return queryset


def ElderStatistic(request):
    def dictfetchall(cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def namedtuplefetchall(cursor):
        "Return all rows from a cursor as a namedtuple"
        desc = cursor.description
        nt_result = namedtuple('Result', [col[0] for col in desc])
        return [nt_result(*row) for row in cursor.fetchall()]

    dict_list = []
    with connection.cursor() as cursor:
        sql = '''
            select 
                CONVERT(varchar(7),TimeOfApplication,111) date
            from old
            where TimeOfApplication is not null
            group by CONVERT(varchar(7),TimeOfApplication,111)
            order by CONVERT(varchar(7),TimeOfApplication,111)
        '''
        cursor.execute(sql_base + sql)
        date_list = cursor.fetchall()

        for date in date_list:
            dict_date = {}
            dict_date['date'] = date
            sql = '''
                select 
                    OrganID id
                    ,OrganName name
                    ,count(*)total
                    ,SUM(case when ReplyState!=0 then 1 else 0 end)success
                    ,SUM(case when ReplyState=0 then 1 else 0 end)failed
                from old
                group by OrganID,OrganName
            '''
            cursor.execute(sql_base + sql)
            dict_date['data'] = dictfetchall(cursor)

            for item in dict_date['data']:
                sql = '''
                    select top 10
                        ROW_NUMBER() over(order by count(*) desc)  id
                        ,Department name
                        ,count(*)value
                    from old
                    where OrganID=%s
                    group by Department
                '''
                cursor.execute(sql_base + sql, [item['id']])
                item['dept'] = dictfetchall(cursor)
                sql = '''
                    select top 10
                        ROW_NUMBER() over(order by count(*) desc) id
                        ,Department name
                        ,count(*)value
                    from old
                    where OrganID=%s
                    group by Department
                '''
                cursor.execute(sql_base + sql, [item['id']])
                item['res_type'] = dictfetchall(cursor)
                sql = '''
                    select top 10
                        UserID id
                        ,UserName name
                        ,Department dept
                        ,count(*)value
                    from old
                    where OrganID=%s
                    group by UserID,UserName,Department
                    order by count(*) desc
                '''
                cursor.execute(sql_base + sql, [item['id']])
                item['custom'] = dictfetchall(cursor)
            date_list.append(dict_date)
    return JsonResponse(date_list)