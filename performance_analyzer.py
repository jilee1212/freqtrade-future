#!/usr/bin/env python3
"""
Performance Analyzer
====================

Phase 6 백테스팅 성능 분석 및 비교 도구
- 전략별 성능 비교
- 리스크 조정 지표 계산
- 포괄적 성능 리포트 생성
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import os
from typing import Dict, List, Optional


class PerformanceAnalyzer:
    """성능 분석기"""

    def __init__(self, results_dir: str = "user_data/backtest_results"):
        self.results_dir = Path(results_dir)
        self.strategies_performance = {}

    def load_backtest_results(self) -> Dict:
        """백테스트 결과 로드"""
        results = {}

        if not self.results_dir.exists():
            print(f"Results directory not found: {self.results_dir}")
            return results

        for file in self.results_dir.glob("*.json"):
            if file.name.endswith('.meta.json'):
                continue

            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    strategy_name = data.get('strategy', {}).get('strategy_name', 'Unknown')
                    results[strategy_name] = data
                    print(f"Loaded results for strategy: {strategy_name}")
            except Exception as e:
                print(f"Error loading {file}: {e}")

        return results

    def calculate_advanced_metrics(self, trades_data: List[Dict]) -> Dict:
        """고급 성능 지표 계산"""
        if not trades_data:
            return self._empty_metrics()

        # 거래 데이터를 DataFrame으로 변환
        df = pd.DataFrame(trades_data)

        # 기본 지표
        total_trades = len(df)
        winning_trades = len(df[df['profit_ratio'] > 0])
        losing_trades = len(df[df['profit_ratio'] < 0])

        if total_trades == 0:
            return self._empty_metrics()

        win_rate = winning_trades / total_trades * 100

        # 수익률 관련
        profit_ratios = df['profit_ratio'].values
        total_return = (1 + profit_ratios).prod() - 1
        avg_return = np.mean(profit_ratios)

        # 리스크 지표
        volatility = np.std(profit_ratios)
        sharpe_ratio = avg_return / volatility if volatility > 0 else 0

        # 최대 낙폭 계산
        cumulative_returns = (1 + df['profit_ratio']).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdowns.min()

        # 연속 손실/이익
        consecutive_losses = self._calculate_consecutive_losses(profit_ratios)
        consecutive_wins = self._calculate_consecutive_wins(profit_ratios)

        # Calmar 비율 (연간 수익률 / 최대 낙폭)
        calmar_ratio = (total_return * 365 / 90) / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino 비율 (하방 위험 조정 수익률)
        downside_returns = profit_ratios[profit_ratios < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino_ratio = avg_return / downside_std if downside_std > 0 else 0

        # 수익 팩터 (총 이익 / 총 손실)
        total_profits = df[df['profit_ratio'] > 0]['profit_ratio'].sum()
        total_losses = abs(df[df['profit_ratio'] < 0]['profit_ratio'].sum())
        profit_factor = total_profits / total_losses if total_losses > 0 else float('inf')

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return': total_return * 100,
            'avg_return': avg_return * 100,
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'profit_factor': profit_factor,
            'consecutive_losses': consecutive_losses,
            'consecutive_wins': consecutive_wins,
            'best_trade': max(profit_ratios) * 100 if profit_ratios.size > 0 else 0,
            'worst_trade': min(profit_ratios) * 100 if profit_ratios.size > 0 else 0
        }

    def _empty_metrics(self) -> Dict:
        """빈 메트릭 딕셔너리"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_return': 0,
            'avg_return': 0,
            'volatility': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'calmar_ratio': 0,
            'sortino_ratio': 0,
            'profit_factor': 0,
            'consecutive_losses': 0,
            'consecutive_wins': 0,
            'best_trade': 0,
            'worst_trade': 0
        }

    def _calculate_consecutive_losses(self, returns: np.ndarray) -> int:
        """연속 손실 계산"""
        max_consecutive = 0
        current_consecutive = 0

        for ret in returns:
            if ret < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _calculate_consecutive_wins(self, returns: np.ndarray) -> int:
        """연속 이익 계산"""
        max_consecutive = 0
        current_consecutive = 0

        for ret in returns:
            if ret > 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def compare_strategies(self, results: Dict) -> pd.DataFrame:
        """전략별 성능 비교"""
        comparison_data = []

        for strategy_name, data in results.items():
            trades = data.get('trades', [])
            metrics = self.calculate_advanced_metrics(trades)

            # 추가 정보 추출
            summary = data.get('results_per_pair', [{}])[0] if data.get('results_per_pair') else {}

            comparison_data.append({
                'Strategy': strategy_name,
                'Total Trades': metrics['total_trades'],
                'Win Rate (%)': f"{metrics['win_rate']:.1f}",
                'Total Return (%)': f"{metrics['total_return']:.2f}",
                'Sharpe Ratio': f"{metrics['sharpe_ratio']:.2f}",
                'Max Drawdown (%)': f"{metrics['max_drawdown']:.2f}",
                'Profit Factor': f"{metrics['profit_factor']:.2f}",
                'Calmar Ratio': f"{metrics['calmar_ratio']:.2f}",
                'Sortino Ratio': f"{metrics['sortino_ratio']:.2f}",
                'Best Trade (%)': f"{metrics['best_trade']:.2f}",
                'Worst Trade (%)': f"{metrics['worst_trade']:.2f}",
                'Max Consecutive Losses': metrics['consecutive_losses'],
                'Volatility (%)': f"{metrics['volatility']:.2f}"
            })

        return pd.DataFrame(comparison_data)

    def generate_performance_report(self, results: Dict) -> str:
        """포괄적 성능 리포트 생성"""

        report = "="*80 + "\n"
        report += "PHASE 6 BACKTESTING PERFORMANCE REPORT\n"
        report += "="*80 + "\n\n"

        report += f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Analysis Period: 90 days (2025-06-30 to 2025-09-28)\n"
        report += f"Strategies Analyzed: {len(results)}\n\n"

        # 전략별 상세 분석
        for i, (strategy_name, data) in enumerate(results.items(), 1):
            trades = data.get('trades', [])
            metrics = self.calculate_advanced_metrics(trades)

            report += f"{i}. {strategy_name.upper()}\n"
            report += "-" * 50 + "\n"

            if metrics['total_trades'] == 0:
                report += "   No trades executed during the period.\n"
                report += "   Strategy may be too conservative or conditions not met.\n\n"
                continue

            # 기본 성과
            report += f"   Trades Executed: {metrics['total_trades']}\n"
            report += f"   Win Rate: {metrics['win_rate']:.1f}% ({metrics['winning_trades']} wins / {metrics['losing_trades']} losses)\n"
            report += f"   Total Return: {metrics['total_return']:+.2f}%\n"
            report += f"   Average Return per Trade: {metrics['avg_return']:+.2f}%\n\n"

            # 리스크 지표
            report += "   RISK METRICS:\n"
            report += f"   - Volatility: {metrics['volatility']:.2f}%\n"
            report += f"   - Maximum Drawdown: {metrics['max_drawdown']:.2f}%\n"
            report += f"   - Sharpe Ratio: {metrics['sharpe_ratio']:.2f}\n"
            report += f"   - Sortino Ratio: {metrics['sortino_ratio']:.2f}\n"
            report += f"   - Calmar Ratio: {metrics['calmar_ratio']:.2f}\n\n"

            # 거래 품질
            report += "   TRADE QUALITY:\n"
            report += f"   - Profit Factor: {metrics['profit_factor']:.2f}\n"
            report += f"   - Best Trade: {metrics['best_trade']:+.2f}%\n"
            report += f"   - Worst Trade: {metrics['worst_trade']:+.2f}%\n"
            report += f"   - Max Consecutive Losses: {metrics['consecutive_losses']}\n"
            report += f"   - Max Consecutive Wins: {metrics['consecutive_wins']}\n\n"

            # 성과 등급
            grade = self._calculate_performance_grade(metrics)
            report += f"   PERFORMANCE GRADE: {grade}\n\n"

        # 전략 비교표
        if len(results) > 1:
            comparison_df = self.compare_strategies(results)
            report += "STRATEGY COMPARISON\n"
            report += "-" * 50 + "\n"
            report += comparison_df.to_string(index=False) + "\n\n"

        # 추천사항
        report += "RECOMMENDATIONS\n"
        report += "-" * 50 + "\n"
        report += self._generate_recommendations(results) + "\n"

        report += "="*80 + "\n"
        report += "End of Report\n"
        report += "="*80 + "\n"

        return report

    def _calculate_performance_grade(self, metrics: Dict) -> str:
        """성과 등급 계산"""
        score = 0

        # 수익률 (40점)
        if metrics['total_return'] > 10:
            score += 40
        elif metrics['total_return'] > 5:
            score += 30
        elif metrics['total_return'] > 0:
            score += 20
        elif metrics['total_return'] > -5:
            score += 10

        # 샤프비율 (30점)
        if metrics['sharpe_ratio'] > 2:
            score += 30
        elif metrics['sharpe_ratio'] > 1:
            score += 25
        elif metrics['sharpe_ratio'] > 0.5:
            score += 15
        elif metrics['sharpe_ratio'] > 0:
            score += 10

        # 승률 (20점)
        if metrics['win_rate'] > 70:
            score += 20
        elif metrics['win_rate'] > 60:
            score += 15
        elif metrics['win_rate'] > 50:
            score += 10
        elif metrics['win_rate'] > 40:
            score += 5

        # 낙폭 (10점)
        if abs(metrics['max_drawdown']) < 5:
            score += 10
        elif abs(metrics['max_drawdown']) < 10:
            score += 7
        elif abs(metrics['max_drawdown']) < 20:
            score += 4

        if score >= 85:
            return "A+ (Excellent)"
        elif score >= 75:
            return "A (Very Good)"
        elif score >= 65:
            return "B (Good)"
        elif score >= 55:
            return "C (Average)"
        elif score >= 45:
            return "D (Below Average)"
        else:
            return "F (Poor)"

    def _generate_recommendations(self, results: Dict) -> str:
        """추천사항 생성"""
        recommendations = []

        if not results:
            return "No strategies to analyze."

        # 전체 분석
        total_strategies = len(results)
        profitable_strategies = 0
        total_trades = 0

        for strategy_name, data in results.items():
            trades = data.get('trades', [])
            metrics = self.calculate_advanced_metrics(trades)
            total_trades += metrics['total_trades']

            if metrics['total_return'] > 0:
                profitable_strategies += 1

        if profitable_strategies == 0:
            recommendations.append("- All strategies showed losses. Consider:")
            recommendations.append("  - Adjusting entry/exit parameters")
            recommendations.append("  - Using different timeframes")
            recommendations.append("  - Adding more pairs for diversification")
            recommendations.append("  - Implementing position sizing optimization")

        if total_trades < 5:
            recommendations.append("- Low trade frequency detected. Consider:")
            recommendations.append("  - Relaxing entry conditions")
            recommendations.append("  - Using shorter timeframes")
            recommendations.append("  - Adding more trading pairs")

        # 개별 전략 추천
        for strategy_name, data in results.items():
            trades = data.get('trades', [])
            metrics = self.calculate_advanced_metrics(trades)

            if metrics['total_trades'] == 0:
                recommendations.append(f"- {strategy_name}: No trades executed")
                recommendations.append("  - Strategy may be too conservative")
                recommendations.append("  - Consider adjusting RSI thresholds")
                recommendations.append("  - Review Bollinger Band parameters")

            elif metrics['win_rate'] < 40:
                recommendations.append(f"- {strategy_name}: Low win rate ({metrics['win_rate']:.1f}%)")
                recommendations.append("  - Review entry conditions")
                recommendations.append("  - Consider tighter stop losses")
                recommendations.append("  - Optimize exit signals")

        # Phase 6 다음 단계
        recommendations.append("\n- NEXT STEPS FOR PHASE 7:")
        recommendations.append("  - Implement web-based dashboard")
        recommendations.append("  - Add real-time monitoring")
        recommendations.append("  - Set up Telegram notifications")
        recommendations.append("  - Prepare for production deployment")

        return "\n".join(recommendations) if recommendations else "Strategies are performing well. Continue monitoring."

    def export_results(self, results: Dict, filename: str = None):
        """결과를 파일로 내보내기"""
        if filename is None:
            filename = f"performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        report = self.generate_performance_report(results)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Performance report saved to: {filename}")


def main():
    """메인 함수"""
    print("Phase 6 Performance Analysis")
    print("=" * 50)

    analyzer = PerformanceAnalyzer()

    # 백테스트 결과 로드
    results = analyzer.load_backtest_results()

    if not results:
        print("No backtest results found.")
        print("Please run backtesting first using:")
        print("freqtrade backtesting --config user_data/backtest_config.json --strategy [STRATEGY_NAME]")
        return

    # 성능 분석 및 리포트 생성
    report = analyzer.generate_performance_report(results)
    print(report)

    # 결과 내보내기
    analyzer.export_results(results)

    # 전략 비교 (여러 전략이 있는 경우)
    if len(results) > 1:
        comparison_df = analyzer.compare_strategies(results)
        print("\nSTRATEGY COMPARISON TABLE:")
        print(comparison_df)


if __name__ == "__main__":
    main()