! Wait for ODB-API to provide Python3 bindings.
!
! ifort -o write_fso_odb.exe write_fso_odb.f90 -I${ODB_API_ROOT}/include -L${ODB_API_ROOT}/lib -lOdb_fortran

program write_fso_odb

  use odbql_wrappers

  implicit none

  real(8), parameter :: real_missing_value = -888888.0
  integer, parameter :: int_missing_value = -88

  type(odbql) odb_db
  type(odbql_stmt) odb_stmt
  character(100) :: odb_unparsed_sql = ''

  character(100) file_path
  character(30) obs_type, tmp_str
  integer num_platform
  integer i, j, k, n, m, tmp_int
  real(8) lon, lat
  real(8) u, u_impact, u_obserr, u_incr; integer u_qc
  real(8) v, v_impact, v_obserr, v_incr; integer v_qc
  real(8) t, t_impact, t_obserr, t_incr; integer t_qc
  real(8) p, p_impact, p_obserr, p_incr; integer p_qc
  real(8) q, q_impact, q_obserr, q_incr; integer q_qc

  call get_command_argument(1, file_path)

  call odbql_open('', odb_db)
  call odbql_prepare_v2(odb_db, 'CREATE TABLE wrf_fso AS (' // &
    'obs_type STRING, '       // &
    'lon REAL, '              // &
    'lat REAL, '              // &
    'u REAL, '                // &
    'u_impact REAL, '         // &
    'u_qc INTEGER, '          // &
    'u_obserr REAL, '         // &
    'u_incr REAL, '           // &
    'v REAL, '                // &
    'v_impact REAL, '         // &
    'v_qc INTEGER, '          // &
    'v_obserr REAL, '         // &
    'v_incr REAL, '           // &
    't REAL, '                // &
    't_impact REAL, '         // &
    't_qc INTEGER, '          // &
    't_obserr REAL, '         // &
    't_incr REAL, '           // &
    'p REAL, '                // &
    'p_impact REAL, '         // &
    'p_qc INTEGER, '          // &
    'p_obserr REAL, '         // &
    'p_incr REAL, '           // &
    'q REAL, '                // &
    'q_impact REAL, '         // &
    'q_qc INTEGER, '          // &
    'q_obserr REAL, '         // &
    'q_incr REAL '            // &
    ') ON "' // trim(file_path) // '.odb";', -1, odb_stmt, odb_unparsed_sql)
  call odbql_prepare_v2(odb_db, 'INSERT INTO wrf_fso (' // &
    'obs_type, '              // &
    'lon, '                   // &
    'lat, '                   // &
    'u, '                     // &
    'u_impact, '              // &
    'u_qc, '                  // &
    'u_obserr, '              // &
    'u_incr, '                // &
    'v, '                     // &
    'v_impact, '              // &
    'v_qc, '                  // &
    'v_obserr, '              // &
    'v_incr, '                // &
    't, '                     // &
    't_impact, '              // &
    't_qc, '                  // &
    't_obserr, '              // &
    't_incr, '                // &
    'p, '                     // &
    'p_impact, '              // &
    'p_qc, '                  // &
    'p_obserr, '              // &
    'p_incr, '                // &
    'q, '                     // &
    'q_impact, '              // &
    'q_qc, '                  // &
    'q_obserr, '              // &
    'q_incr '                 // &
    ') VALUES (' // odb_values_placeholder(28) // ');', -1, odb_stmt, odb_unparsed_sql)

  open(10, file=file_path, status='old')
  do i = 1, 6
    read(10, *, end=10) obs_type, num_platform
    if (obs_type == 'sonde_sfc') then
      obs_type = 'sondesfc'
    end if
    write(*, *) '[Notice]: Process ', num_platform, trim(obs_type), ' ...'
    do j = 1, num_platform
      read(10, *) n
      do k = 1, n
        u = real_missing_value; u_impact = real_missing_value; u_qc = int_missing_value; u_obserr = real_missing_value; u_incr = real_missing_value
        v = real_missing_value; v_impact = real_missing_value; v_qc = int_missing_value; v_obserr = real_missing_value; v_incr = real_missing_value
        t = real_missing_value; t_impact = real_missing_value; t_qc = int_missing_value; t_obserr = real_missing_value; t_incr = real_missing_value
        p = real_missing_value; p_impact = real_missing_value; p_qc = int_missing_value; p_obserr = real_missing_value; p_incr = real_missing_value
        q = real_missing_value; q_impact = real_missing_value; q_qc = int_missing_value; q_obserr = real_missing_value; q_incr = real_missing_value
        select case (obs_type)
        case ('synop', 'metar', 'ships', 'buoy', 'sondesfc')
          read(10, *) tmp_int, tmp_str, lat, lon, p, &
                      u, u_impact, u_qc, u_obserr, u_incr, &
                      v, v_impact, v_qc, v_obserr, v_incr, &
                      t, t_impact, t_qc, t_obserr, t_incr, &
                      p, p_impact, p_qc, p_obserr, p_incr, &
                      q, q_impact, q_qc, q_obserr, q_incr
        case ('sound', 'airep')
          read(10, *) tmp_int, tmp_str, lat, lon, p, &
                      u, u_impact, u_qc, u_obserr, u_incr, &
                      v, v_impact, v_qc, v_obserr, v_incr, &
                      t, t_impact, t_qc, t_obserr, t_incr, &
                      q, q_impact, q_qc, q_obserr, q_incr
        case default
          write(*, *) '[Error]: Unsupported obs_type ' // trim(obs_type) // '!'
          stop 1
        end select
        m = 0
        m = m + 1; call odbql_bind_text  (odb_stmt, m, trim(obs_type), len_trim(obs_type))
        m = m + 1; call odbql_bind_double(odb_stmt, m, dble(lon))
        m = m + 1; call odbql_bind_double(odb_stmt, m, dble(lat))
        m = m + 1; if (u        /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(u))
        m = m + 1; if (u_impact /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(u_impact))
        m = m + 1; if (u_qc     /=  int_missing_value) call odbql_bind_int   (odb_stmt, m, u_qc)
        m = m + 1; if (u_obserr /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(u_obserr))
        m = m + 1; if (u_incr   /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(u_incr))
        m = m + 1; if (v        /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(v))
        m = m + 1; if (v_impact /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(v_impact))
        m = m + 1; if (v_qc     /=  int_missing_value) call odbql_bind_int   (odb_stmt, m, v_qc)
        m = m + 1; if (v_obserr /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(v_obserr))
        m = m + 1; if (v_incr   /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(v_incr))
        m = m + 1; if (t        /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(t))
        m = m + 1; if (t_impact /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(t_impact))
        m = m + 1; if (t_qc     /=  int_missing_value) call odbql_bind_int   (odb_stmt, m, t_qc)
        m = m + 1; if (t_obserr /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(t_obserr))
        m = m + 1; if (t_incr   /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(t_incr))
        m = m + 1; if (p        /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(p))
        m = m + 1; if (p_impact /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(p_impact))
        m = m + 1; if (p_qc     /=  int_missing_value) call odbql_bind_int   (odb_stmt, m, p_qc)
        m = m + 1; if (p_obserr /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(p_obserr))
        m = m + 1; if (p_incr   /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(p_incr))
        m = m + 1; if (q        /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(q))
        m = m + 1; if (q_impact /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(q_impact))
        m = m + 1; if (q_qc     /=  int_missing_value) call odbql_bind_int   (odb_stmt, m, q_qc)
        m = m + 1; if (q_obserr /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(q_obserr))
        m = m + 1; if (q_incr   /= real_missing_value) call odbql_bind_double(odb_stmt, m, dble(q_incr))
        call odbql_step(odb_stmt)
        call odb_all_bind_null(odb_stmt, m)
      end do
    end do
  end do
10  close(10)

  call odbql_finalize(odb_stmt)
  call odbql_close(odb_db)

contains

  function odb_values_placeholder(n) result(res)

    integer, intent(in) :: n
    character(:), allocatable :: res

    character(n * 2 - 1) tmp

    integer i

    do i = 1, n - 1
      tmp(2*i-1:2*i) = '?,'
    end do
    tmp(2*n-1:2*n-1) = '?'
    res = tmp

  end function odb_values_placeholder

  subroutine odb_all_bind_null(odb_stmt, n)

    type(odbql_stmt), intent(in) :: odb_stmt
    integer, intent(in) :: n

    integer i

    do i = 1, n
      call odbql_bind_null(odb_stmt, i)
    end do

  end subroutine odb_all_bind_null


end program write_fso_odb
