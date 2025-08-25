#!/usr/bin/env python3

import requests
import json
import base64
import time
from datetime import datetime, timedelta

class DoorayMCPTester:
    def __init__(self, base_url="http://localhost:8000", token="km1h1gv5u8kd:aMD-hc5gRzuUx5CcOXyTmw"):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        self.issues = []
        self.drive_id = None
        self.project_id = None
        self.wiki_id = None
        
    def log_issue(self, category, description, details=None):
        """문제점 기록"""
        issue = {
            "category": category,
            "description": description,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.issues.append(issue)
        print(f"❌ [{category}] {description}")
        if details:
            print(f"   세부사항: {details}")
    
    def log_success(self, category, description):
        """성공 기록"""
        print(f"✅ [{category}] {description}")
    
    def test_auth(self):
        """인증 관련 테스트"""
        print("\n🔑 인증 시스템 테스트")
        print("=" * 40)
        
        try:
            # 1. 토큰 설정
            response = self.session.post(f"{self.base_url}/mcp/auth/set_token",
                headers={"Content-Type": "application/json"},
                json={"token": self.token})
            
            if response.status_code == 200 and response.json().get("success"):
                self.log_success("AUTH", "토큰 설정 성공")
            else:
                self.log_issue("AUTH", "토큰 설정 실패", response.json())
                return False
            
            # 2. 토큰 상태 확인
            response = self.session.get(f"{self.base_url}/mcp/auth/status")
            result = response.json()
            
            if result.get("authenticated") and result.get("token_valid"):
                self.log_success("AUTH", "토큰 인증 상태 정상")
            else:
                self.log_issue("AUTH", "토큰 인증 상태 비정상", result)
                return False
                
            return True
            
        except Exception as e:
            self.log_issue("AUTH", "인증 테스트 중 예외 발생", str(e))
            return False
    
    def test_drive_apis(self):
        """드라이브 API 전체 테스트"""
        print("\n📁 드라이브 API 테스트")
        print("=" * 40)
        
        try:
            # 1. 드라이브 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/drive/list",
                headers={"Content-Type": "application/json"},
                json={"type": "private"})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                drives = result.get("result", {}).get("result", [])
                if drives:
                    self.drive_id = drives[0]["id"]
                    self.log_success("DRIVE", f"드라이브 목록 조회 성공 (총 {len(drives)}개)")
                else:
                    self.log_issue("DRIVE", "드라이브 목록이 비어있음")
                    return False
            else:
                self.log_issue("DRIVE", "드라이브 목록 조회 실패", result)
                return False
            
            # 2. 드라이브 파일 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/drive/files/list",
                headers={"Content-Type": "application/json"},
                json={"drive_id": self.drive_id})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                files = result.get("result", {}).get("result", [])
                self.log_success("DRIVE", f"파일 목록 조회 성공 (총 {len(files)}개)")
                
                # 테스트 파일이 있는지 확인
                test_files = [f for f in files if f.get("name", "").startswith("dooray_test_")]
                if test_files:
                    self.log_success("DRIVE", f"이전 업로드 테스트 파일 확인됨 ({len(test_files)}개)")
                    
                    # 3. 파일 메타데이터 조회 테스트
                    test_file = test_files[0]
                    response = self.session.post(f"{self.base_url}/mcp/drive/files/metadata",
                        headers={"Content-Type": "application/json"},
                        json={"drive_id": self.drive_id, "file_id": test_file["id"]})
                    
                    result = response.json()
                    if result.get("header", {}).get("isSuccessful"):
                        self.log_success("DRIVE", "파일 메타데이터 조회 성공")
                    else:
                        self.log_issue("DRIVE", "파일 메타데이터 조회 실패", result)
                    
                    # 4. 파일 다운로드 테스트 (새로운 download_complete API)
                    response = self.session.post(f"{self.base_url}/mcp/drive/files/download_complete",
                        headers={"Content-Type": "application/json"},
                        json={"drive_id": self.drive_id, "file_id": test_file["id"]})
                    
                    result = response.json()
                    if result.get("success") and result.get("dooray_response", {}).get("fileData"):
                        file_data = result["dooray_response"]["fileData"]
                        download_type = result["dooray_response"].get("downloadType")
                        self.log_success("DRIVE", f"파일 다운로드 성공 (타입: {download_type}, 크기: {len(file_data)} chars)")
                    else:
                        self.log_issue("DRIVE", "파일 다운로드 실패", result)
                
            else:
                self.log_issue("DRIVE", "파일 목록 조회 실패", result)
            
            # 5. 새 파일 업로드 테스트
            test_content = f"종합 테스트 파일 - {datetime.now().isoformat()}"
            test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
            
            response = self.session.post(f"{self.base_url}/mcp/drive/files/upload",
                headers={"Content-Type": "application/json"},
                json={
                    "drive_id": self.drive_id,
                    "folder_id": "4139443628284755447",  # 테스트 폴더
                    "file_name": "comprehensive_test.txt",
                    "file_content_base64": test_content_b64
                })
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                uploaded_file_id = result.get("result", {}).get("result", {}).get("id")
                self.log_success("DRIVE", f"파일 업로드 성공 (ID: {uploaded_file_id})")
                
                # 업로드한 파일 삭제 테스트
                if uploaded_file_id:
                    time.sleep(1)  # 잠시 대기
                    response = self.session.post(f"{self.base_url}/mcp/drive/files/delete",
                        headers={"Content-Type": "application/json"},
                        json={"drive_id": self.drive_id, "file_id": uploaded_file_id})
                    
                    result = response.json()
                    if result.get("header", {}).get("isSuccessful"):
                        self.log_success("DRIVE", "파일 삭제 성공")
                    else:
                        self.log_issue("DRIVE", "파일 삭제 실패", result)
            else:
                self.log_issue("DRIVE", "파일 업로드 실패", result)
            
            return True
            
        except Exception as e:
            self.log_issue("DRIVE", "드라이브 API 테스트 중 예외 발생", str(e))
            return False
    
    def test_project_apis(self):
        """프로젝트 API 테스트"""
        print("\n📋 프로젝트 API 테스트")
        print("=" * 40)
        
        try:
            # 1. 프로젝트 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/project/list",
                headers={"Content-Type": "application/json"},
                json={})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                projects = result.get("result", {}).get("result", [])
                if projects:
                    self.project_id = projects[0]["id"]
                    self.log_success("PROJECT", f"프로젝트 목록 조회 성공 (총 {len(projects)}개)")
                else:
                    self.log_issue("PROJECT", "프로젝트 목록이 비어있음")
                    return False
            else:
                self.log_issue("PROJECT", "프로젝트 목록 조회 실패", result)
                return False
            
            # 2. 프로젝트 상세 조회
            response = self.session.post(f"{self.base_url}/mcp/project/get",
                headers={"Content-Type": "application/json"},
                json={"project_id": self.project_id})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                self.log_success("PROJECT", "프로젝트 상세 조회 성공")
            else:
                self.log_issue("PROJECT", "프로젝트 상세 조회 실패", result)
            
            # 3. 프로젝트 멤버 조회
            response = self.session.post(f"{self.base_url}/mcp/project/members/list",
                headers={"Content-Type": "application/json"},
                json={"project_id": self.project_id})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                members = result.get("result", {}).get("result", [])
                self.log_success("PROJECT", f"프로젝트 멤버 조회 성공 (총 {len(members)}명)")
            else:
                self.log_issue("PROJECT", "프로젝트 멤버 조회 실패", result)
            
            # 4. 업무 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/project/posts/list",
                headers={"Content-Type": "application/json"},
                json={"project_id": self.project_id})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                posts = result.get("result", {}).get("result", [])
                self.log_success("PROJECT", f"업무 목록 조회 성공 (총 {len(posts)}개)")
            else:
                self.log_issue("PROJECT", "업무 목록 조회 실패", result)
            
            # 5. 새 업무 생성 테스트
            response = self.session.post(f"{self.base_url}/mcp/project/posts/create",
                headers={"Content-Type": "application/json"},
                json={
                    "project_id": self.project_id,
                    "subject": f"종합 테스트 업무 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "body": "MCP 서버 종합 테스트를 위한 자동 생성 업무입니다."
                })
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                created_post_id = result.get("result", {}).get("result", {}).get("id")
                self.log_success("PROJECT", f"업무 생성 성공 (ID: {created_post_id})")
                
                # 생성한 업무에 댓글 추가 테스트
                if created_post_id:
                    time.sleep(1)  # 잠시 대기
                    response = self.session.post(f"{self.base_url}/mcp/project/posts/comments/create",
                        headers={"Content-Type": "application/json"},
                        json={
                            "project_id": self.project_id,
                            "post_id": created_post_id,
                            "content": "자동 테스트로 생성된 댓글입니다."
                        })
                    
                    result = response.json()
                    if result.get("header", {}).get("isSuccessful"):
                        self.log_success("PROJECT", "업무 댓글 생성 성공")
                    else:
                        self.log_issue("PROJECT", "업무 댓글 생성 실패", result)
            else:
                self.log_issue("PROJECT", "업무 생성 실패", result)
            
            return True
            
        except Exception as e:
            self.log_issue("PROJECT", "프로젝트 API 테스트 중 예외 발생", str(e))
            return False
    
    def test_wiki_apis(self):
        """위키 API 테스트"""
        print("\n📚 위키 API 테스트")
        print("=" * 40)
        
        try:
            # 1. 위키 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/wiki/list",
                headers={"Content-Type": "application/json"},
                json={})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                wikis = result.get("result", {}).get("result", [])
                if wikis:
                    self.wiki_id = wikis[0]["id"]
                    self.log_success("WIKI", f"위키 목록 조회 성공 (총 {len(wikis)}개)")
                else:
                    self.log_issue("WIKI", "위키 목록이 비어있음")
                    return False
            else:
                self.log_issue("WIKI", "위키 목록 조회 실패", result)
                return False
            
            # 2. 위키 페이지 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/wiki/pages/list",
                headers={"Content-Type": "application/json"},
                json={"wiki_id": self.wiki_id})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                pages = result.get("result", {}).get("result", [])
                self.log_success("WIKI", f"위키 페이지 목록 조회 성공 (총 {len(pages)}개)")
            else:
                self.log_issue("WIKI", "위키 페이지 목록 조회 실패", result)
            
            # 3. 새 위키 페이지 생성 테스트
            response = self.session.post(f"{self.base_url}/mcp/wiki/pages/create",
                headers={"Content-Type": "application/json"},
                json={
                    "wiki_id": self.wiki_id,
                    "title": f"종합 테스트 페이지 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "content": "# MCP 서버 종합 테스트\n\n이것은 자동 테스트로 생성된 위키 페이지입니다.\n\n## 테스트 내용\n- API 연동 테스트\n- 위키 페이지 생성 테스트"
                })
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                created_page_id = result.get("result", {}).get("result", {}).get("id")
                self.log_success("WIKI", f"위키 페이지 생성 성공 (ID: {created_page_id})")
            else:
                self.log_issue("WIKI", "위키 페이지 생성 실패", result)
            
            return True
            
        except Exception as e:
            self.log_issue("WIKI", "위키 API 테스트 중 예외 발생", str(e))
            return False
    
    def test_calendar_apis(self):
        """캘린더 API 테스트"""
        print("\n📅 캘린더 API 테스트")
        print("=" * 40)
        
        try:
            # 1. 캘린더 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/calendar/list",
                headers={"Content-Type": "application/json"},
                json={})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                calendars = result.get("result", {}).get("result", [])
                if calendars:
                    calendar_id = calendars[0]["id"]
                    self.log_success("CALENDAR", f"캘린더 목록 조회 성공 (총 {len(calendars)}개)")
                    
                    # 2. 캘린더 일정 조회
                    response = self.session.post(f"{self.base_url}/mcp/calendar/events/list",
                        headers={"Content-Type": "application/json"},
                        json={"calendar_id": calendar_id})
                    
                    result = response.json()
                    if result.get("header", {}).get("isSuccessful"):
                        events = result.get("result", {}).get("result", [])
                        self.log_success("CALENDAR", f"캘린더 일정 조회 성공 (총 {len(events)}개)")
                    else:
                        self.log_issue("CALENDAR", "캘린더 일정 조회 실패", result)
                    
                    # 3. 새 일정 생성 테스트
                    tomorrow = datetime.now() + timedelta(days=1)
                    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(hours=1)
                    
                    response = self.session.post(f"{self.base_url}/mcp/calendar/events/create",
                        headers={"Content-Type": "application/json"},
                        json={
                            "calendar_id": calendar_id,
                            "subject": f"MCP 테스트 회의 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            "started_at": start_time.isoformat() + "Z",
                            "ended_at": end_time.isoformat() + "Z",
                            "body": "MCP 서버 종합 테스트를 위한 자동 생성 일정입니다."
                        })
                    
                    result = response.json()
                    if result.get("header", {}).get("isSuccessful"):
                        created_event_id = result.get("result", {}).get("result", {}).get("id")
                        self.log_success("CALENDAR", f"캘린더 일정 생성 성공 (ID: {created_event_id})")
                    else:
                        self.log_issue("CALENDAR", "캘린더 일정 생성 실패", result)
                        
                else:
                    self.log_issue("CALENDAR", "캘린더 목록이 비어있음")
                    return False
            else:
                self.log_issue("CALENDAR", "캘린더 목록 조회 실패", result)
                return False
            
            return True
            
        except Exception as e:
            self.log_issue("CALENDAR", "캘린더 API 테스트 중 예외 발생", str(e))
            return False
    
    def test_messenger_apis(self):
        """메신저 API 테스트"""
        print("\n💬 메신저 API 테스트")
        print("=" * 40)
        
        try:
            # 1. 멤버 목록 조회 (메시지 수신자 찾기용)
            response = self.session.post(f"{self.base_url}/mcp/common/members/list",
                headers={"Content-Type": "application/json"},
                json={})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                members = result.get("result", {}).get("result", [])
                if members:
                    self.log_success("MESSENGER", f"멤버 목록 조회 성공 (총 {len(members)}명)")
                else:
                    self.log_issue("MESSENGER", "멤버 목록이 비어있음")
                    return False
            else:
                self.log_issue("MESSENGER", "멤버 목록 조회 실패", result)
                return False
            
            # 실제 메시지 전송은 스킵 (다른 사용자에게 스팸이 될 수 있음)
            self.log_success("MESSENGER", "메시지 전송 기능은 스킵 (스팸 방지)")
            
            return True
            
        except Exception as e:
            self.log_issue("MESSENGER", "메신저 API 테스트 중 예외 발생", str(e))
            return False
    
    def test_common_apis(self):
        """공통 API 테스트 (멤버, 훅 등)"""
        print("\n👥 공통 API 테스트")
        print("=" * 40)
        
        try:
            # 1. 멤버 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/common/members/list",
                headers={"Content-Type": "application/json"},
                json={})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                members = result.get("result", {}).get("result", [])
                self.log_success("COMMON", f"멤버 목록 조회 성공 (총 {len(members)}명)")
                
                # 첫 번째 멤버 상세 조회
                if members:
                    first_member = members[0]
                    member_id = first_member.get("organizationMemberId")
                    
                    if member_id:
                        response = self.session.post(f"{self.base_url}/mcp/common/members/get",
                            headers={"Content-Type": "application/json"},
                            json={"member_id": member_id})
                        
                        result = response.json()
                        if result.get("header", {}).get("isSuccessful"):
                            self.log_success("COMMON", "멤버 상세 조회 성공")
                        else:
                            self.log_issue("COMMON", "멤버 상세 조회 실패", result)
            else:
                self.log_issue("COMMON", "멤버 목록 조회 실패", result)
            
            # 2. 인커밍 훅 목록 조회
            response = self.session.post(f"{self.base_url}/mcp/hooks/incoming/list",
                headers={"Content-Type": "application/json"},
                json={})
            
            result = response.json()
            if result.get("header", {}).get("isSuccessful"):
                hooks = result.get("result", {}).get("result", [])
                self.log_success("COMMON", f"인커밍 훅 목록 조회 성공 (총 {len(hooks)}개)")
            else:
                self.log_issue("COMMON", "인커밍 훅 목록 조회 실패", result)
            
            return True
            
        except Exception as e:
            self.log_issue("COMMON", "공통 API 테스트 중 예외 발생", str(e))
            return False
    
    def generate_report(self):
        """테스트 결과 리포트 생성"""
        print("\n" + "=" * 60)
        print("📊 종합 테스트 결과 리포트")
        print("=" * 60)
        
        if not self.issues:
            print("🎉 모든 테스트 통과! 문제점 없음")
        else:
            print(f"⚠️ 총 {len(self.issues)}개 문제점 발견:")
            print()
            
            # 카테고리별 분류
            by_category = {}
            for issue in self.issues:
                category = issue["category"]
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(issue)
            
            for category, category_issues in by_category.items():
                print(f"🔍 [{category}] {len(category_issues)}개 문제:")
                for i, issue in enumerate(category_issues, 1):
                    print(f"  {i}. {issue['description']}")
                    if issue["details"]:
                        print(f"     → {issue['details']}")
                print()
        
        # 결과를 파일로 저장
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "issues": self.issues
        }
        
        with open("mcp_test_report.json", "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📝 상세 리포트가 'mcp_test_report.json'에 저장되었습니다.")
        
        return len(self.issues) == 0
    
    def run_comprehensive_test(self):
        """전체 테스트 실행"""
        print("🚀 Dooray MCP 서버 종합 테스트 시작")
        print("=" * 60)
        
        # 각 테스트 실행
        tests = [
            ("인증", self.test_auth),
            ("드라이브", self.test_drive_apis),
            ("프로젝트", self.test_project_apis),
            ("위키", self.test_wiki_apis),
            ("캘린더", self.test_calendar_apis),
            ("메신저", self.test_messenger_apis),
            ("공통", self.test_common_apis)
        ]
        
        passed_tests = 0
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                time.sleep(2)  # 테스트 간 대기
            except Exception as e:
                self.log_issue(test_name.upper(), f"{test_name} 테스트 중 치명적 오류", str(e))
        
        # 최종 리포트
        success = self.generate_report()
        
        print("\n" + "=" * 60)
        print(f"🏁 테스트 완료: {passed_tests}/{len(tests)} 카테고리 통과")
        
        if success:
            print("✅ 모든 기능이 정상 동작합니다!")
        else:
            print("❌ 일부 기능에 문제가 있습니다. 수정이 필요합니다.")
        
        return success

if __name__ == "__main__":
    tester = DoorayMCPTester()
    tester.run_comprehensive_test()