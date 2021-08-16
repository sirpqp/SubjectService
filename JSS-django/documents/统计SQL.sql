with a as (
	select 
		DATEADD(HH,8,api_request.date_registered) date_registered,
		DATEADD(HH,8,api_task.data_replied)data_replied,
		api_task.status,
		api_restype.name res_type,
		api_customer.nickname custom,api_customer.dept,
		api_group.id,api_group.name,api_group.organ_id,
		api_organ.name oname,
		reg.id reg_id,reg.nickname reg_name,
		reply.id reply_id,reply.nickname reply_name
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

--日活 分时 总量 成功率
--select 
--    ROW_NUMBER() over(order by COUNT(*)) id,
--    COUNT(*) total,
--    (select COUNT(*) from a where DATEDIFF(day,date_registered,getdate())=0) today,
--    (select COUNT(*) from a where DATEDIFF(day,date_registered,getdate()-1)=0) yesterday,
--    (select COUNT(*) from a where DATEDIFF(day,date_registered,getdate()-7)=0) week,
--	(select count(distinct CONVERT(varchar(10),date_registered,111)) from a) days,
--    (select MAX(total) from (select count(*)total from a where DATEDIFF(MONTH,date_registered,getdate())=0 group by CONVERT(varchar(10),date_registered,111))b) max
--from a
--select 
--	ROW_NUMBER() over(order by CONVERT(varchar(10),date_registered,111)) id,
--	CONVERT(varchar(10),date_registered,111) date,
--	DATEPART(HOUR,date_registered) hour,
--	COUNT(*) total
--from a
--where DATEDIFF(day,date_registered,getdate())=0
--group by CONVERT(varchar(10),date_registered,111),DATEPART(HOUR,date_registered)
--order by CONVERT(varchar(10),date_registered,111),DATEPART(HOUR,date_registered)
--select 
--    ROW_NUMBER() over(order by COUNT(*)) id,
--    COUNT(*) total,
--    (select COUNT(*) from a where DATEDIFF(day,date_registered,getdate())=0 and status='success') today,
--    (select COUNT(*) from a where DATEDIFF(day,date_registered,getdate()-1)=0 and status='success') yesterday,
--    (select COUNT(*) from a where DATEDIFF(day,date_registered,getdate()-7)=0 and status='success') week
--from a
--where status='success'

--员工工作情况
--select 
--    ROW_NUMBER() over(order by reg_id) id,
--    reg_name,
--    COUNT(*) total
--from a
--where reg_id in (3,4,5,6,7,8) and (date_registered between '2020-08-31' and '2020-09-06')
--group by reg_id,reg_name
--select 
--	CONVERT(varchar(10),date_registered,111) date,
--	reg_name,
--	COUNT(*) total
--from a
--group by CONVERT(varchar(10),date_registered,111),reg_name
--order by CONVERT(varchar(10),date_registered,111)
select 
	ROW_NUMBER() over(order by CONVERT(varchar(10),date_registered,111)) id,
	CONVERT(varchar(10),date_registered,111) date,
	COUNT(*)total,
	SUM(case status when 'success' then 1 end)success
from a
select DATEADD(day,1,CONVERT(varchar(10),getdate(),111))

--select 
--	CONVERT(varchar(10),data_replied,111) date,
--	reply_name,
--	COUNT(*) total
--from a
--where data_replied is not null
--group by CONVERT(varchar(10),data_replied,111),reply_name
--order by CONVERT(varchar(10),data_replied,111)

--活跃情况
--select 
--	ROW_NUMBER() over(order by COUNT(*) desc) id,
--	name,
--	COUNT(*) total
--from a
--group by name
--select 
--	ROW_NUMBER() over(order by date) id,
--	date,
--	COUNT(*) total
--from (
--	select top 100 percent
--		CONVERT(varchar(10),date_registered,111)date,
--		custom
--	from a 
--	group by CONVERT(varchar(10),date_registered,111),custom
--	order by CONVERT(varchar(10),date_registered,111)
--	)b
--group by date
--select 
--	CONVERT(varchar(10),date_registered,111) date,
--	name,
--	COUNT(*) total
--from a
--group by CONVERT(varchar(10),date_registered,111),name
--order by CONVERT(varchar(10),date_registered,111),COUNT(*) desc

--资源比
--select
--	ROW_NUMBER() over(order by COUNT(*) desc) id,
--	res_type,
--	COUNT(*) total
--from a
--where res_type is not NULL
--group by res_type

--机构
--select 
--	organ_id id,
--	oname name,
--	COUNT(*) total
--from a
--where oname like '%%'
--group by organ_id,oname
--order by COUNT(*) desc

--select 
--	ROW_NUMBER() over(order by COUNT(*) desc) id,
--	dept type,
--	count(*) value
--from a
--where organ_id=50
--group by dept
--select
--	1id,
--	(select COUNT(*) from a where organ_id=50 and status='success')success,
--	(select COUNT(*) from a where organ_id=50 and status!='success')failed
--select 
--	ROW_NUMBER() over(order by COUNT(*) desc) id,
--	(case when res_type is null then '其他' else res_type end) type,
--	COUNT(*)sales 
--from a
--where organ_id=50
--group by res_type
--select 
--	ROW_NUMBER() over(order by COUNT(*) desc) id,
--	custom name,
--	(case when dept is null then '其他' else dept end)dept,
--	COUNT(*)total from a
--where organ_id=50
--group by custom,dept