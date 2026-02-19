"""
memory_cleaner.py - KIVOSY 메모리 응급 청소 도구
Factory Manager专用 - 잘못된 학습 데이터를 강제 삭제/수정
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class MemoryCleaner:
    """
    메모리 청소 전문가 - 잘못된 환상 데이터를 강제 삭제!
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.learning_file = self.memory_dir / 'learning.json'
        self.preferences_file = self.memory_dir / 'preferences.json'
        self.backup_file = self.memory_dir / f'learning_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    def clean_false_facts(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        잘못된 사실들을 청소합니다.
        
        Args:
            dry_run: True면 실제 저장 안 함 (시뮬레이션)
        
        Returns:
            청소 결과 리포트
        """
        print("🧹 KIVOSY 메모리 청소 시작...")
        
        # 1. 현재 메모리 로드
        learning = self._load_json(self.learning_file)
        if not learning:
            print("❌ learning.json을 찾을 수 없음")
            return {"error": "file not found"}
        
        # 2. 백업 생성
        if not dry_run:
            self._backup(learning)
        
        # 3. MASTER TRUTH TABLE
        MASTER_TRUTHS = {
            # owner_identity: 공장장은 비서가 아니다!
            "owner_is_not_secretary": [
                "공장장은 비서",
                "공장장의 직업은 비서",
                "공장장이 비서",
                "직업은 비서"
            ],
            # iu_is_singer: 아이유는 가수!
            "iu_is_singer": [
                "아이유는 유튜버",
                "아이유 유튜버"
            ],
            # jarvis_is_secretary: 자비스는 비서!
            "jarvis_role": [
                "자비스는 주인"
            ]
        }
        
        # 4. 사실들 검사 및 청소
        facts = learning.get('facts', [])
        cleaned_facts = []
        removed_count = 0
        corrected_count = 0
        
        for fact in facts:
            content = fact.get('content', '')
            fact_type = fact.get('type', '')
            
            # 검사 플래그
            needs_removal = False
            needs_correction = False
            corrected_content = content
            
            # MASTER TRUTH 위반 검사
            if any(bad_phrase in content for bad_phrase in MASTER_TRUTHS["owner_is_not_secretary"]):
                if "공장장" in content and "비서" in content:
                    if not ("주인" in content or "사장" in content or "공장장" != "비서"):
                        print(f"🚨 발견: 잘못된 신분 정보 - {content}")
                        needs_removal = True
                        removed_count += 1
            
            if any(bad_phrase in content for bad_phrase in MASTER_TRUTHS["iu_is_singer"]):
                if "아이유" in content and "유튜버" in content:
                    print(f"🚨 발견: 아이유 환각 - {content}")
                    needs_removal = True
                    removed_count += 1
            
            # Confidence가 너무 낮은 것도 정리
            confidence = fact.get('confidence', 0.5)
            if confidence < 0.3 and len(content) < 10:  # 의미 없는 낮은 신뢰도 사실
                print(f"🗑️ 제거: 낮은 신뢰도 사실 - {content}")
                needs_removal = True
                removed_count += 1
            
            if not needs_removal:
                cleaned_facts.append(fact)
        
        # 5. 학습 데이터 업데이트
        learning['facts'] = cleaned_facts
        
        # 6. preferences.json도 확인 (user role)
        prefs = self._load_json(self.preferences_file)
        if prefs:
            user = prefs.get('user', {})
            if user.get('role') == 'Secretary' or user.get('role') == '비서':
                print(f"🚨 preferences.json에 잘못된 role 발견: {user.get('role')}")
                if not dry_run:
                    user['role'] = 'Factory Owner'
                    prefs['user'] = user
                    self._save_json(self.preferences_file, prefs)
                    print("✅ preferences.json 복구 완료")
        
        # 7. 저장
        if not dry_run:
            self._save_json(self.learning_file, learning)
            print(f"✅ 메모리 저장 완료! {removed_count}개 제거, {corrected_count}개 수정")
        else:
            print(f"📝 [Dry Run] 제거 대상: {removed_count}개, 수정 대상: {corrected_count}개")
            print("💡 실제 적용하려면 dry_run=False로 실행하세요")
        
        return {
            "removed": removed_count,
            "corrected": corrected_count,
            "remaining": len(cleaned_facts),
            "dry_run": dry_run
        }
    
    def add_master_truth(self, truth_type: str, truth_content: str, dry_run: bool = True):
        """
        MASTER TRUTH를 learning.json에 강제 추가 (삭제되지 않음)
        """
        learning = self._load_json(self.learning_file)
        
        # MASTER TRUTH 섹션 추가
        if 'master_truths' not in learning:
            learning['master_truths'] = []
        
        # 중복 체크
        for truth in learning['master_truths']:
            if truth.get('type') == truth_type:
                print(f"⚠️ 이미 존재하는 MASTER TRUTH: {truth_type}")
                return
        
        # 추가
        learning['master_truths'].append({
            'type': truth_type,
            'content': truth_content,
            'added_at': datetime.now().isoformat(),
            'confidence': 1.0,
            'immutable': True  # 절대 삭제 불가 표시
        })
        
        if not dry_run:
            self._save_json(self.learning_file, learning)
            print(f"✅ MASTER TRUTH 추가됨: {truth_type}")
        else:
            print(f"📝 [Dry Run] MASTER TRUTH 추가 예정: {truth_type}")
    
    def _load_json(self, path):
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ 로드 실패 {path}: {e}")
        return {}
    
    def _save_json(self, path, data):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 저장 실패 {path}: {e}")
    
    def _backup(self, data):
        """청소 전 백업"""
        try:
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 백업 생성됨: {self.backup_file}")
        except Exception as e:
            print(f"⚠️ 백업 실패: {e}")


# 실행 스크립트
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='KIVOSY 메모리 청소 도구')
    parser.add_argument('--execute', action='store_true', help='실제 실행 (기본은 dry run)')
    parser.add_argument('--add-truth', nargs=2, metavar=('TYPE', 'CONTENT'), help='MASTER TRUTH 추가')
    
    args = parser.parse_args()
    
    cleaner = MemoryCleaner()
    
    if args.add_truth:
        truth_type, truth_content = args.add_truth
        cleaner.add_master_truth(truth_type, truth_content, dry_run=not args.execute)
    
    # 청소 실행
    result = cleaner.clean_false_facts(dry_run=not args.execute)
    
    print(f"\n📊 청소 결과:")
    print(f"   제거된 사실: {result['removed']}개")
    print(f"   남은 사실: {result['remaining']}개")