create view public.licenses_needing_reminders as
with
  reminder_status as (
    select
      l.id,
      l.lic_name,
      l.lic_type,
      l.lic_state,
      l.expiration_date,
      l.lic_notify_names,
      l.email_enabled,
      l.expiration_date - CURRENT_DATE as days_until_expiration,
      case
        when (l.expiration_date - CURRENT_DATE) = 60 then '60_days'::text
        when (l.expiration_date - CURRENT_DATE) = 30 then '30_days'::text
        when (l.expiration_date - CURRENT_DATE) = 15 then '15_days'::text
        when (l.expiration_date - CURRENT_DATE) = 7 then '7_days'::text
        when (l.expiration_date - CURRENT_DATE) = 1 then '1_day'::text
        when l.expiration_date < CURRENT_DATE then 'overdue_daily'::text
        else null::text
      end as reminder_type
    from
      licenses l
    where
      l.expiration_date is not null
      and l.lic_notify_names is not null
      and l.lic_notify_names <> ''::text
      and l.email_enabled = true
      and (
        (
          (l.expiration_date - CURRENT_DATE) = any (array[60, 30, 15, 7, 1])
        )
        or l.expiration_date < CURRENT_DATE
      )
  ),
  recent_reminders as (
    select
      er.license_id,
      er.reminder_type,
      max(er.sent_date) as last_sent_date
    from
      email_reminders er
    where
      date (er.sent_date) >= (CURRENT_DATE - '7 days'::interval)
    group by
      er.license_id,
      er.reminder_type
  )
select
  rs.id,
  rs.lic_name,
  rs.lic_type,
  rs.lic_state,
  rs.expiration_date,
  rs.lic_notify_names,
  rs.email_enabled,
  rs.days_until_expiration,
  rs.reminder_type
from
  reminder_status rs
  left join recent_reminders rr on rs.id = rr.license_id
  and rs.reminder_type = rr.reminder_type
  and (
    (
      rs.reminder_type = any (
        array[
          '60_days'::text,
          '30_days'::text,
          '15_days'::text,
          '7_days'::text,
          '1_day'::text
        ]
      )
    )
    and date (rr.last_sent_date) = CURRENT_DATE
    or rs.reminder_type = 'overdue_daily'::text
    and date (rr.last_sent_date) = CURRENT_DATE
  )
where
  rr.license_id is null
order by
  rs.days_until_expiration,
  rs.lic_name;




create view public.overdue_licenses as
select
  l.id,
  l.lic_name,
  l.lic_state,
  l.lic_type,
  l.lic_no,
  l.ascem_no,
  l.first_issue_date,
  l.expiration_date,
  l.lic_notify_names,
  l.created_at,
  l.updated_at,
  CURRENT_DATE - l.expiration_date as days_overdue
from
  licenses l
where
  l.expiration_date is not null
  and l.expiration_date < CURRENT_DATE
order by
  l.expiration_date;


create view public.upcoming_expirations as
select
  l.id,
  l.lic_name,
  l.lic_state,
  l.lic_type,
  l.lic_no,
  l.ascem_no,
  l.first_issue_date,
  l.expiration_date,
  l.lic_notify_names,
  l.created_at,
  l.updated_at,
  l.expiration_date - CURRENT_DATE as days_until_expiration,
  case
    when (l.expiration_date - CURRENT_DATE) <= 10 then 'critical'::text
    when (l.expiration_date - CURRENT_DATE) <= 30 then 'warning'::text
    when (l.expiration_date - CURRENT_DATE) <= 60 then 'upcoming'::text
    else 'normal'::text
  end as status_category
from
  licenses l
where
  l.expiration_date is not null
  and l.expiration_date >= CURRENT_DATE
  and l.expiration_date <= (CURRENT_DATE + '90 days'::interval)
order by
  l.expiration_date;