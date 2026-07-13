import json
import csv
import os
from datetime import datetime

class DataExporter:
    def __init__(self, config):
        self.config = config

    def export_json(self, data, filepath):
        clean = []
        for item in data:
            entry = {
                'full_name': item['full_name'],
                'name': item['name'],
                'description': item.get('description', ''),
                'url': item.get('url', item.get('html_url', '')),
                'stars': item.get('stars', 0),
                'forks': item.get('forks', 0),
                'language': item.get('language', ''),
                'owner': item.get('owner', ''),
                'platforms': item.get('analysis', {}).get('platforms_detected', []),
                'risk_score': item.get('analysis', {}).get('risk_score', 0),
                'risk_level': item.get('analysis', {}).get('risk_level', 'low'),
                'purpose': item.get('analysis', {}).get('estimated_purpose', 'unknown'),
                'topics': item.get('topics', []),
                'created_at': item.get('created_at', ''),
                'updated_at': item.get('updated_at', ''),
                'score': item.get('_rank_score', 0),
            }
            clean.append(entry)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(clean, f, indent=4, ensure_ascii=False)
        return filepath

    def export_csv(self, data, filepath):
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Full Name', 'Name', 'Description', 'URL', 'Stars', 'Forks',
                'Language', 'Owner', 'Platforms', 'Risk Score', 'Risk Level',
                'Purpose', 'Topics', 'Rank Score'
            ])
            for item in data:
                platforms = ', '.join(item.get('analysis', {}).get('platforms_detected', []))
                topics = ', '.join(item.get('topics', []))
                writer.writerow([
                    item['full_name'],
                    item['name'],
                    item.get('description', ''),
                    item.get('url', item.get('html_url', '')),
                    item.get('stars', 0),
                    item.get('forks', 0),
                    item.get('language', ''),
                    item.get('owner', ''),
                    platforms,
                    item.get('analysis', {}).get('risk_score', 0),
                    item.get('analysis', {}).get('risk_level', 'low'),
                    item.get('analysis', {}).get('estimated_purpose', 'unknown'),
                    topics,
                    item.get('_rank_score', 0),
                ])
        return filepath

    def export_report(self, data, filepath):
        lines = []
        lines.append("=" * 78)
        lines.append("  GHOST VIPER - INTELLIGENCE REPORT")
        lines.append(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Repos found: {len(data)}")
        lines.append("=" * 78)
        lines.append("")

        for i, item in enumerate(data[:50], 1):
            analysis = item.get('analysis', {})
            lines.append(f"  [{i:02d}] {item['full_name']}")
            lines.append(f"        ⭐ {item.get('stars', 0)} | 🍴 {item.get('forks', 0)} | {item.get('language', '?')}")
            lines.append(f"        {item.get('description', '(no description)')}")
            lines.append(f"        Platforms: {', '.join(analysis.get('platforms_detected', ['?']) or ['?'])}")
            lines.append(f"        Risk: {analysis.get('risk_score', 0)}% [{analysis.get('risk_level', 'unknown').upper()}]")
            lines.append(f"        Type: {analysis.get('estimated_purpose', 'unknown')}")
            if analysis.get('features'):
                lines.append(f"        Features: {', '.join(analysis['features'][:5])}")
            lines.append(f"        {item.get('url', item.get('html_url', ''))}")
            lines.append("")

        lines.append("=" * 78)
        lines.append("  END OF REPORT")
        lines.append("=" * 78)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return filepath

    def export_full(self, data, base_name=None):
        if base_name is None:
            base_name = f"ghost_viper_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        out_dir = os.path.join(self.config['clone_dir'] if 'clone_dir' in self.config.__dict__ else os.path.expanduser('~'), 'exports')
        os.makedirs(out_dir, exist_ok=True)

        files = {}
        files['json'] = self.export_json(data, os.path.join(out_dir, f"{base_name}.json"))
        files['csv'] = self.export_csv(data, os.path.join(out_dir, f"{base_name}.csv"))
        files['report'] = self.export_report(data, os.path.join(out_dir, f"{base_name}.txt"))
        return files
