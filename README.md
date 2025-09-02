# Dooray MCP Server for ChatGPT

이 프로젝트는 FastAPI를 기반으로 구축된 Dooray MCP(Model Context Protocol) 서버입니다. ChatGPT와 같은 AI 모델이 Dooray API와 연동하여 다양한 작업을 수행할 수 있도록 중개자 역할을 합니다.

## 🚀 기능

이 MCP 서버는 현재 다음과 같은 Dooray API 기능을 제공합니다:

### Common API
- **멤버 목록 조회**: Dooray 조직의 멤버 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/common/members/list`
  - 요청 본문: `{}`
- **멤버 상세 조회**: 특정 멤버의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/common/members/get`
  - 요청 본문: `{"member_id": "<멤버 ID>"}`
- **Incoming Hook 생성**: 새로운 Incoming Hook을 생성합니다.
  - 엔드포인트: `POST /mcp/common/incoming_hooks/create`
  - 요청 본문: `{"name": "<훅 이름>", "url": "<훅 URL>", "description": "<설명 (선택 사항)>"}`
- **Incoming Hook 조회**: 특정 Incoming Hook의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/common/incoming_hooks/get`
  - 요청 본문: `{"incoming_hook_id": "<훅 ID>"}`
- **Incoming Hook 삭제**: 특정 Incoming Hook을 삭제합니다.
  - 엔드포인트: `POST /mcp/common/incoming_hooks/delete`
  - 요청 본문: `{"incoming_hook_id": "<훅 ID>"}`

### Admin API
- **멤버 추가**: 새로운 멤버를 추가합니다. (관리자 권한 필요)
  - 엔드포인트: `POST /mcp/admin/members/create`
  - 요청 본문: `{"member_data": {"userId": "<사용자 ID>", "name": "<이름>", "email": "<이메일>", "departmentId": "<부서 ID>", ...}}`
- **멤버 목록 조회**: 관리자 권한으로 멤버 목록을 조회합니다. (관리자 권한 필요)
  - 엔드포인트: `GET /mcp/admin/members`
  - 요청 본문: `{}`
- **멤버 수정**: 특정 멤버의 정보를 수정합니다. (관리자 권한 필요)
  - 엔드포인트: `POST /mcp/admin/members/update`
  - 요청 본문: `{"member_id": "<멤버 ID>", "member_data": {"name": "<새 이름 (선택 사항)>", ...}}`
- **멤버 퇴사 처리**: 특정 멤버를 퇴사 처리합니다. (관리자 권한 필요)
  - 엔드포인트: `POST /mcp/admin/members/leave`
  - 요청 본문: `{"member_id": "<멤버 ID>"}`

### 드라이브 API
- **드라이브 목록 조회**: 사용자의 개인 드라이브 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/drive/list`
  - 요청 본문: `{"type": "private"}` (기본값: `private`, `public` 등)
- **드라이브 상세 조회**: 특정 드라이브의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/drive/get`
  - 요청 본문: `{"drive_id": "<드라이브 ID>"}`
- **드라이브 파일 목록 조회**: 특정 드라이브의 파일 및 폴더 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/drive/files/list`
  - 요청 본문: `{"drive_id": "<드라이브 ID>"}`
- **드라이브 파일 메타데이터 조회**: 특정 드라이브 파일의 메타데이터를 조회합니다.
  - 엔드포인트: `POST /mcp/drive/files/metadata`
  - 요청 본문: `{"drive_id": "<드라이브 ID>", "file_id": "<파일 ID>"}`
- **드라이브 파일 다운로드**: 특정 드라이브 파일을 다운로드합니다.
  - 엔드포인트: `POST /mcp/drive/files/download`
  - 요청 본문: `{"drive_id": "<드라이브 ID>", "file_id": "<파일 ID>"}`

### 메신저 API
- **메신저 1:1 메시지 전송**: 특정 사용자에게 1:1 메시지를 전송합니다.
  - 엔드포인트: `POST /mcp/messenger/send`
  - 요청 본문: `{"recipient_id": "<Dooray 조직 멤버 ID>", "message": "<메시지 내용>"}`

### 프로젝트/업무 API
- **프로젝트 목록 조회**: 접근 가능한 프로젝트 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/project/list`
  - 요청 본문: `{}`
- **프로젝트 생성**: 새로운 프로젝트를 생성합니다.
  - 엔드포인트: `POST /mcp/project/create`
  - 요청 본문: `{"name": "<프로젝트 이름>", "code": "<프로젝트 코드>", "description": "<프로젝트 설명 (선택 사항)>"}`
- **프로젝트 상세 조회**: 특정 프로젝트의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/project/get`
  - 요청 본문: `{"project_id": "<프로젝트 ID>"}`
- **프로젝트 멤버 목록 조회**: 특정 프로젝트의 멤버 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/project/members/list`
  - 요청 본문: `{"project_id": "<프로젝트 ID>"}`
- **프로젝트 멤버 상세 조회**: 특정 프로젝트의 특정 멤버 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/project/members/get`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "member_id": "<멤버 ID>"}`
- **프로젝트 생성 가능 여부 확인**: 프로젝트 생성이 가능한지 여부를 확인합니다.
  - 엔드포인트: `POST /mcp/project/is_creatable`
  - 요청 본문: `{}`
- **프로젝트 워크플로우 목록 조회**: 특정 프로젝트의 워크플로우 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/project/workflows/list`
  - 요청 본문: `{"project_id": "<프로젝트 ID>"}`
- **프로젝트 워크플로우 생성**: 특정 프로젝트에 새로운 워크플로우를 생성합니다.
  - 엔드포인트: `POST /mcp/project/workflows/create`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "name": "<워크플로우 이름>", "description": "<설명 (선택 사항)>"}`
- **프로젝트 워크플로우 수정**: 특정 프로젝트의 워크플로우를 수정합니다.
  - 엔드포인트: `POST /mcp/project/workflows/update`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "workflow_id": "<워크플로우 ID>", "name": "<새 이름 (선택 사항)>", "description": "<새 설명 (선택 사항)>"}`
- **프로젝트 워크플로우 삭제**: 특정 프로젝트의 워크플로우를 삭제합니다.
  - 엔드포인트: `POST /mcp/project/workflows/delete`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "workflow_id": "<워크플로우 ID>"}`
- **업무 목록 조회**: 특정 프로젝트의 업무 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/project/posts/list`
  - 요청 본문: `{"project_id": "<프로젝트 ID>"}`
- **업무 상세 조회**: 특정 업무의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/project/posts/get`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "post_id": "<업무 ID>"}`
- **업무 생성**: 특정 프로젝트에 새로운 업무를 생성합니다.
  - 엔드포인트: `POST /mcp/project/posts/create`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "subject": "<업무 제목>", "body": "<업무 내용 (선택 사항)>", "post_type": "task"}` (기본값: `task`, `milestone` 등)
- **업무 수정**: 특정 업무의 제목 또는 내용을 수정합니다.
  - 엔드포인트: `POST /mcp/project/posts/update`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "post_id": "<업무 ID>", "subject": "<새 업무 제목 (선택 사항)>", "body": "<새 업무 내용 (선택 사항)>"}`
- **업무 상태 변경**: 특정 업무의 워크플로우 상태를 변경합니다.
  - 엔드포인트: `POST /mcp/project/posts/update_workflow`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "post_id": "<업무 ID>", "workflow_id": "<워크플로우 ID>"}`
- **업무 완료 처리**: 특정 업무를 완료 상태로 변경합니다.
  - 엔드포인트: `POST /mcp/project/posts/set_done`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "post_id": "<업무 ID>"}`
- **업무 댓글 생성**: 특정 업무에 댓글을 생성합니다.
  - 엔드포인트: `POST /mcp/project/comments/create`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "post_id": "<업무 ID>", "content": "<댓글 내용>"}`
- **업무 댓글 목록 조회**: 특정 업무의 댓글 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/project/comments/list`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "post_id": "<업무 ID>"}`
- **업무 댓글 수정**: 특정 업무 댓글의 내용을 수정합니다.
  - 엔드포인트: `POST /mcp/project/comments/update`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "post_id": "<업무 ID>", "comment_id": "<댓글 ID>", "content": "<새 댓글 내용>"}`
- **업무 댓글 삭제**: 특정 업무 댓글을 삭제합니다.
  - 엔드포인트: `POST /mcp/project/comments/delete`
  - 요청 본문: `{"project_id": "<프로젝트 ID>", "post_id": "<업무 ID>", "comment_id": "<댓글 ID>"}`

### 위키 API
- **위키 목록 조회**: 접근 가능한 위키 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/wiki/list`
  - 요청 본문: `{}`
- **위키 페이지 목록 조회**: 특정 위키의 페이지 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/list`
  - 요청 본문: `{"wiki_id": "<위키 ID>"}`
- **위키 페이지 상세 조회**: 특정 위키 페이지의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/get`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>"}`
- **위키 페이지 생성**: 새로운 위키 페이지를 생성합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/create`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "title": "<페이지 제목>", "content": "<페이지 내용>", "parent_page_id": "<부모 페이지 ID (선택 사항)>"}`
- **위키 페이지 수정**: 특정 위키 페이지의 제목 또는 내용을 수정합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/update`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "title": "<새 페이지 제목 (선택 사항)>", "content": "<새 페이지 내용 (선택 사항)>"}`
- **위키 페이지 제목 수정**: 특정 위키 페이지의 제목만 수정합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/update_title`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "title": "<새 페이지 제목>"}`
- **위키 페이지 내용 수정**: 특정 위키 페이지의 내용만 수정합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/update_content`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "content": "<새 페이지 내용>"}`
- **위키 페이지 참조자 수정**: 특정 위키 페이지의 참조자를 수정합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/update_referrers`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "referrers": ["<참조자 ID 1>", "<참조자 ID 2>"]}`
- **위키 페이지 댓글 생성**: 특정 위키 페이지에 댓글을 생성합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/comments/create`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "content": "<댓글 내용>"}`
- **위키 페이지 댓글 목록 조회**: 특정 위키 페이지의 댓글 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/comments/list`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>"}`
- **위키 페이지 댓글 상세 조회**: 특정 위키 페이지의 특정 댓글 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/comments/get`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "comment_id": "<댓글 ID>"}`
- **위키 페이지 댓글 수정**: 특정 위키 페이지 댓글의 내용을 수정합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/comments/update`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "comment_id": "<댓글 ID>", "content": "<새 댓글 내용>"}`
- **위키 페이지 댓글 삭제**: 특정 위키 페이지 댓글을 삭제합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/comments/delete`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "comment_id": "<댓글 ID>"}`
- **위키 페이지 파일 업로드**: 특정 위키 페이지에 파일을 업로드합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/files/upload`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "file_name": "<파일 이름>", "file_content_base64": "<Base64 인코딩된 파일 내용>"}`
- **위키 페이지 파일 조회**: 특정 위키 페이지의 파일 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/files/get`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "file_id": "<파일 ID>"}`
- **위키 페이지 파일 삭제**: 특정 위키 페이지의 파일을 삭제합니다.
  - 엔드포인트: `POST /mcp/wiki/pages/files/delete`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "page_id": "<페이지 ID>", "file_id": "<파일 ID>"}`
- **위키 파일 업로드**: 위키에 파일을 업로드합니다. (페이지에 종속되지 않음)
  - 엔드포인트: `POST /mcp/wiki/files/upload`
  - 요청 본문: `{"wiki_id": "<위키 ID>", "file_name": "<파일 이름>", "file_content_base64": "<Base64 인코딩된 파일 내용>"}`

### 캘린더 API
- **캘린더 목록 조회**: 사용자의 캘린더 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/calendar/list`
  - 요청 본문: `{}`
- **캘린더 상세 조회**: 특정 캘린더의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/calendar/get`
  - 요청 본문: `{"calendar_id": "<캘린더 ID>"}`
- **일정 생성**: 새로운 일정을 생성합니다.
  - 엔드포인트: `POST /mcp/calendar/events/create`
  - 요청 본문: `{"calendar_id": "<캘린더 ID>", "subject": "<일정 제목>", "started_at": "<시작 시간 (ISO 8601)>", "ended_at": "<종료 시간 (ISO 8601)>", "body": "<일정 내용 (선택 사항)>", "location": "<장소 (선택 사항)>", "users": [{"type": "member", "member": {"organizationMemberId": "<참여자 ID>"}}]}`
- **일정 목록 조회**: 특정 캘린더의 일정 목록을 조회합니다. (`*`는 모든 캘린더)
  - 엔드포인트: `POST /mcp/calendar/events/list`
  - 요청 본문: `{"calendar_id": "<캘린더 ID (선택 사항, 기본값: *)>", "time_min": "<시작 시간 (ISO 8601, 선택 사항)>", "time_max": "<종료 시간 (ISO 8601, 선택 사항)>"}`
- **일정 상세 조회**: 특정 일정의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/calendar/events/get`
  - 요청 본문: `{"calendar_id": "<캘린더 ID>", "event_id": "<일정 ID>"}`
- **일정 수정**: 특정 일정의 정보를 수정합니다.
  - 엔드포인트: `POST /mcp/calendar/events/update`
  - 요청 본문: `{"calendar_id": "<캘린더 ID>", "event_id": "<일정 ID>", "subject": "<새 일정 제목 (선택 사항)>", ...}`
- **일정 삭제**: 특정 일정을 삭제합니다.
  - 엔드포인트: `POST /mcp/calendar/events/delete`
  - 요청 본문: `{"calendar_id": "<캘린더 ID>", "event_id": "<일정 ID>"}`

### 예약 API
- **자원 카테고리 조회**: 예약 가능한 자원 카테고리 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/reservation/categories/list`
  - 요청 본문: `{}`
- **자원 목록 조회**: 예약 가능한 자원 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/reservation/resources/list`
  - 요청 본문: `{}`
- **자원 상세 조회**: 특정 자원의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/reservation/resources/get`
  - 요청 본문: `{"resource_id": "<자원 ID>"}`
- **자원 예약 목록 조회**: 자원 예약 목록을 조회합니다.
  - 엔드포인트: `POST /mcp/reservation/list`
  - 요청 본문: `{}`
- **자원 예약 생성**: 새로운 자원 예약을 생성합니다.
  - 엔드포인트: `POST /mcp/reservation/create`
  - 요청 본문: `{"resource_id": "<자원 ID>", "subject": "<예약 제목>", "started_at": "<시작 시간 (ISO 8601)>", "ended_at": "<종료 시간 (ISO 8601)>", "users": [{"type": "member", "member": {"organizationMemberId": "<참여자 ID>"}}]}`
- **자원 예약 상세 조회**: 특정 자원 예약의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/reservation/get`
  - 요청 본문: `{"resource_reservation_id": "<자원 예약 ID>"}`
- **자원 예약 수정**: 특정 자원 예약의 정보를 수정합니다.
  - 엔드포인트: `POST /mcp/reservation/update`
  - 요청 본문: `{"resource_reservation_id": "<자원 예약 ID>", "resource_id": "<새 자원 ID (선택 사항)>", ...}`
- **자원 예약 삭제**: 특정 자원 예약을 삭제합니다.
  - 엔드포인트: `POST /mcp/reservation/delete`
  - 요청 본문: `{"resource_reservation_id": "<자원 예약 ID>"}`

### 조직도 API
- **조직도 전체 조회**: Dooray 조직의 전체 조직도를 조회합니다.
  - 엔드포인트: `POST /mcp/organization_chart/list`
  - 요청 본문: `{"include_inactive": <비활성 사용자 포함 여부 (boolean, 기본값: false)>}`
- **부서 상세 조회**: 특정 부서의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/organization_chart/departments/get`
  - 요청 본문: `{"department_id": "<부서 ID>"}`
- **사용자 상세 조회**: 특정 사용자의 상세 정보를 조회합니다.
  - 엔드포인트: `POST /mcp/organization_chart/users/get`
  - 요청 본문: `{"user_id": "<사용자 ID>"}`

### 계정 동기화 API
- **사용자 계정 동기화**: 외부 시스템의 사용자 계정을 Dooray와 동기화합니다.
  - 엔드포인트: `POST /mcp/account_sync/users/sync`
  - 요청 본문: `{"users": [{"user_id": "<사용자 ID>", "name": "<이름>", "email": "<이메일>", "department_id": "<부서 ID>", ...}]}`
- **부서 정보 동기화**: 외부 시스템의 부서 정보를 Dooray와 동기화합니다.
  - 엔드포인트: `POST /mcp/account_sync/departments/sync`
  - 요청 본문: `{"departments": [{"department_id": "<부서 ID>", "name": "<부서 이름>", "parent_department_id": "<부모 부서 ID (선택 사항)>"}]}`
- **동기화된 사용자 계정 삭제**: 이전에 동기화된 사용자 계정을 Dooray에서 삭제합니다.
  - 엔드포인트: `POST /mcp/account_sync/users/delete`
  - 요청 본문: `{"user_id": "<사용자 ID>"}`
- **동기화된 부서 삭제**: 이전에 동기화된 부서를 Dooray에서 삭제합니다.
  - 엔드포인트: `POST /mcp/account_sync/departments/delete`
  - 요청 본문: `{"department_id": "<부서 ID>"}`

## 🔑 인증 방식

이 MCP 서버는 **Dooray 개인 인증 토큰**을 사용하여 API를 인증합니다. 이 토큰은 ChatGPT Connector에서 **API Key 형태로 HTTP 요청 헤더를 통해 전달**됩니다.

1.  **Dooray 개인 인증 토큰 발급**: Dooray 웹 인터페이스에서 `개인 설정 > API > 개인 인증 토큰` 메뉴로 이동하여 토큰을 발급받습니다.
2.  **ChatGPT Connector 설정**: 발급받은 토큰을 ChatGPT Connector 설정 시 API Key 입력란에 입력합니다. ChatGPT는 이 값을 MCP 서버로 보내는 HTTP 요청의 `X-API-Key` 또는 `Authorization: Bearer <API_KEY>` 헤더에 포함하여 전달합니다.

    ```dotenv
    # 공공 두레이 사용자의 경우, 기본 URL을 설정할 수 있습니다.
    # DOORAY_BASE_URL=https://api.gov-dooray.com
    ```

## ⚙️ 설치 및 실행

### 로컬에서 실행

1.  **저장소 클론**: 이 저장소를 로컬에 클론합니다.
    ```bash
    git clone <repository_url>
    cd dooray-mcp-fastapi
    ```
2.  **의존성 설치**: `requirements.txt`에 명시된 Python 패키지를 설치합니다.
    ```bash
    pip install -r requirements.txt
    # 또는 pip3 install -r requirements.txt
    ```
3.  **.env 파일 설정 (선택 사항)**: `DOORAY_BASE_URL`을 설정할 수 있습니다. `DOORAY_ACCESS_TOKEN`은 더 이상 `.env` 파일에서 읽지 않습니다.
4.  **서버 실행**: Uvicorn을 사용하여 FastAPI 애플리케이션을 실행합니다.
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
    서버가 `http://0.0.0.0:8000`에서 실행됩니다.

### Docker를 사용하여 배포

1.  **.env 파일 설정 (선택 사항)**: `DOORAY_BASE_URL`을 설정할 수 있습니다. `DOORAY_ACCESS_TOKEN`은 더 이상 `.env` 파일에서 읽지 않습니다.
2.  **Docker 이미지 빌드**: 프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 Docker 이미지를 빌드합니다.
    ```bash
    docker build -t dooray-mcp-server .
    ```
3.  **Docker 컨테이너 실행**: 빌드된 이미지를 사용하여 컨테이너를 실행합니다.
    ```bash
    docker run -d -p 8000:8000 --env-file ./.env dooray-mcp-server
    ```
    컨테이너가 백그라운드에서 실행되며, 호스트의 8000번 포트와 연결됩니다.

## 🤖 ChatGPT Connector 설정 (가정)

ChatGPT에서 이 MCP 서버를 Connector로 연결하려면, 다음과 유사한 설정을 사용합니다. (ChatGPT의 실제 UI에 따라 다를 수 있습니다.)

1.  **Connector URL**: MCP 서버가 배포된 공개 URL을 입력합니다. (예: `https://your-mcp-server.com`)
2.  **인증 방식**: `API Key` 또는 유사한 옵션을 선택합니다.
3.  **API Key 입력**: `DOORAY_ACCESS_TOKEN`에 설정한 개인 인증 토큰 값을 입력합니다. ChatGPT는 이 값을 MCP 서버로 보내는 HTTP 요청의 `X-API-Key` 또는 `Authorization: Bearer <API_KEY>` 헤더에 포함하여 전달합니다.

## 💡 사용 예시 (ChatGPT 프롬프트)

ChatGPT에서 이 MCP 서버를 연결한 후, 다음과 같이 프롬프트를 사용하여 Dooray API 기능을 호출할 수 있습니다. (ChatGPT의 기능 호출 방식에 따라 프롬프트는 달라질 수 있습니다.)

- **드라이브 목록 조회**: "내 두레이 드라이브 목록 보여줘."
- **드라이브 파일 목록 조회**: "<드라이브 ID> 드라이브의 파일 목록을 보여줘."
- **드라이브 파일 메타데이터 조회**: "<드라이브 ID> 드라이브의 <파일 ID> 파일의 메타데이터를 보여줘."
- **드라이브 파일 다운로드**: "<드라이브 ID> 드라이브의 <파일 ID> 파일을 다운로드해줘."
- **프로젝트 목록 조회**: "두레이 프로젝트 목록 보여줘."
- **업무 생성**: "<개발팀 프로젝트>에 '새로운 기능 개발'이라는 업무를 생성해줘. 내용은 '사용자 피드백 반영'이야."
- **위키 페이지 생성**: "<팀 위키 프로젝트>에 '새로운 기능 문서'라는 위키 페이지를 만들어줘. 내용은 '이 문서는 새로운 기능에 대한 설명입니다.'야."
- **일정 생성**: "내일 오전 10시에 '팀 주간 회의' 일정을 만들어줘. 장소는 '회의실 A'이고, 내용은 '주간 업무 보고'야."
- **자원 예약**: "내일 오후 2시에 '회의실 B'를 1시간 동안 예약해줘. 제목은 '프로젝트 브레인스토밍'이야."
- **조직도 전체 조회**: "두레이 조직도 전체를 보여줘. 비활성 사용자도 포함해줘."
- **부서 상세 조회**: "<부서 ID> 부서의 상세 정보를 알려줘."
- **사용자 상세 조회**: "<사용자 ID> 사용자의 상세 정보를 알려줘."
- **멤버 추가**: "새로운 멤버를 두레이에 추가해줘. 사용자 ID는 'newuser', 이름은 '새로운 사용자', 이메일은 'newuser@example.com', 부서 ID는 'dept123'이야."
- **멤버 퇴사 처리**: "'olduser' ID를 가진 멤버를 퇴사 처리해줘."

## ⚠️ 중요 사항

- **Dooray API 엔드포인트 및 본문 형식**: `dooray_client.py`에 구현된 모든 API의 엔드포인트와 요청 본문 형식은 제공해주신 문서를 기반으로 합니다. **공공 두레이의 정확한 API 문서를 다시 한번 확인하여 필요에 따라 수정해야 합니다.** 특히 `users` 필드와 같은 복잡한 객체는 정확한 `organizationMemberId` 등을 필요로 합니다.
- **보안**: `DOORAY_ACCESS_TOKEN`은 민감한 정보이므로, `.env` 파일을 Git 저장소에 커밋하지 않도록 주의하십시오. Docker 배포 시 `--env-file` 옵션을 사용하거나, 환경 변수를 안전하게 관리하는 방법을 사용하십시오.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## MCP API

### `initialize`

```bash
curl -s -X POST https://mcp.auraoys.xyz/mcp \
  -H 'Content-Type: application/json' \
  -d '{ "jsonrpc":"2.0", "id":1, "method":"initialize", "params":{} }' | jq .
```

### `tools/list`

```bash
curl -s -X POST https://mcp.auraoys.xyz/mcp \
  -H 'Content-Type: application/json' \
  -d '{ "jsonrpc":"2.0", "id":2, "method":"tools/list", "params":{} }' | jq .
```

### `tools/call` (Example: getProjects)

```bash
curl -s -X POST https://mcp.auraoys.xyz/mcp \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${DOORAY_API_TOKEN}" \
  -d '{ "jsonrpc":"2.0", "id":3, "method":"tools/call", "params":{ "name":"dooray.getProjects", "arguments":{"limit":20} } }' | jq .
```