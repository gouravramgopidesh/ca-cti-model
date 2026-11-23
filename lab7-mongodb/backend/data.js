// Seed records are clearly marked as training examples; they are not live IOCs.
const sources = [
  { name: 'CISA Known Exploited Vulnerabilities', type: 'government', url: 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog', reliability: 98 },
  { name: 'The Hacker News', type: 'news', url: 'https://thehackernews.com/', reliability: 85 },
  { name: 'SANS Internet Storm Center', type: 'research', url: 'https://isc.sans.edu/', reliability: 93 },
  { name: 'NVD', type: 'government', url: 'https://nvd.nist.gov/', reliability: 96 },
  { name: 'CISA Alerts', type: 'government', url: 'https://www.cisa.gov/news-events/cybersecurity-advisories', reliability: 98 }
];
const templates = [
  ['Credential phishing campaign targets cloud accounts', 'phishing', 'high', 'A simulated intelligence brief describing credential-harvesting infrastructure targeting cloud sign-in pages. Validate indicators against trusted feeds before action.', 'The Hacker News', ['credential theft','cloud','initial access'], 'T1566.002'],
  ['Ransomware operators exploit exposed remote access', 'ransomware', 'critical', 'Training example: an intrusion pattern involving exposed remote access, lateral movement, and data-encryption behavior.', 'CISA Alerts', ['ransomware','remote access','extortion'], 'T1133'],
  ['New vulnerability exploitation activity reported', 'vulnerability', 'high', 'Training example for vulnerability triage. Check the vendor advisory and authoritative vulnerability catalog for current status.', 'CISA Known Exploited Vulnerabilities', ['exploitation','patching','vulnerability'], 'T1190'],
  ['Malicious loader delivered through trojanized installer', 'malware', 'medium', 'Synthetic report describing a malware delivery chain for interface and query testing; no executable content or real IOC is included.', 'SANS Internet Storm Center', ['loader','malware','execution'], 'T1204.002'],
  ['Lookalike domain used in business email compromise', 'phishing', 'high', 'Training example about domain impersonation and payment-redirection attempts. Independently verify domains before blocking.', 'The Hacker News', ['BEC','impersonation','email'], 'T1583.001'],
  ['Public-facing application scanning increases', 'reconnaissance', 'medium', 'Synthetic situational update illustrating broad scanning activity against internet-facing services.', 'SANS Internet Storm Center', ['scanning','reconnaissance','exposure'], 'T1595.002'],
  ['Botnet activity abuses weakly protected IoT devices', 'botnet', 'high', 'Training brief describing automated discovery and abuse of exposed edge devices.', 'CISA Alerts', ['botnet','IoT','command and control'], 'T1584.005'],
  ['Vulnerability advisory requires urgent review', 'vulnerability', 'critical', 'Synthetic advisory record for demonstrating severity filters and analyst classification workflows.', 'NVD', ['CVE','patching','exploitation'], 'T1190']
];
function buildArticles(count=24) {
  return Array.from({length:count}, (_,i) => {
    const t=templates[i%templates.length], source=sources.find(s=>s.name===t[4]);
    const day=(i%28)+1;
    return {
      title: i<templates.length?t[0]:`${t[0]} — analyst brief ${String(i+1).padStart(3,'0')}`,
      summary:t[3],
      category:t[1],
      severity:t[2],
      publishedAt:new Date(Date.now()-day*3600_000).toISOString(),
      sourceId:source.name,
      sourceName:source.name,
      sourceUrl:source.url,
      source:{name:source.name,url:source.url,type:source.type,reliability:source.reliability},
      sourceAssessment:{verdict:'needs-review'},
      tags:t[5],
      mitreTechnique:t[6],
      classification:'needs-review',
      isTrainingData:true,
      confidence:72+(i*7%27)
    };
  });
}
module.exports={sources,buildArticles};
