import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
import numpy as np

# Phase 3 Dataset: 13 Incidents (10 Valid, 3 Highly Tricky Noise)
data_list = [
    # Incident 11 [VALID] - Date: 2026-07-01
    ("Security: Logistics crunch worsens as renewed highway kidnappings drive up North-Bound haulage costs", "2026-07-01"),
    ("Terror on Abuja-Kaduna road: Bandits block highway, abduct 22 travelers", "2026-07-01"),
    ("Escape from hell: How 22 commuters were dragged into forest along Abuja-Kaduna express", "2026-07-01"),
    ("Abuja-Kaduna highway under siege again as bandits intercept commercial buses, cart away 22", "2026-07-01"),
    ("The return of highway banditry: Why securing the Abuja-Kaduna transit corridor remains elusive", "2026-07-01"),
    ("National Assembly summons Service Chiefs over fresh abduction of 22 citizens on Abuja-Kaduna road", "2026-07-01"),
    ("Screams on the highway: Bandits shoot tyres, kidnap 22 passengers in broad daylight", "2026-07-01"),
    ("Commuters panic as bandits kidnap 22 on Abuja-Kaduna expressway", "2026-07-01"),
    ("Armed men abduct 22 passengers along Abuja-Kaduna highway", "2026-07-01"),
    ("INVESTIGATION: Security loopholes that allowed bandits to operate for 40 minutes on Abuja-Kaduna highway", "2026-07-01"),

    # Incident 12 [VALID] - Date: 2026-07-02
    ("Military spending efficiency questioned as ISWAP tactical ambushes disrupt Lake Chad regional trade", "2026-07-02"),
    ("Bloodbath in Borno: ISWAP terrorists ambush military convoy, kill 12 soldiers", "2026-07-02"),
    ("Heavy sorrow: 12 gallant soldiers slaughtered in ruthless Boko Haram forest ambush", "2026-07-02"),
    ("Counter-insurgency setback: 12 troops martyred in fierce Borno clash with terrorists", "2026-07-02"),
    ("Reassessing military asymmetric warfare capabilities after Borno convoy ambush claims 12 troops", "2026-07-02"),
    ("DHQ coordinates massive air reprisal after ISWAP ambush kills 12 soldiers in Borno", "2026-07-02"),
    ("Borno ambush: How terrorists used IEDs, RPGs to wipe out military patrol team, killing 12", "2026-07-02"),
    ("12 soldiers feared dead as terrorists attack military convoy in Borno", "2026-07-02"),
    ("12 soldiers killed in ISWAP ambush in Borno state", "2026-07-02"),
    ("EXCLUSIVE: How insider leakage led to the fatal ambush of 12 soldiers in Borno forest", "2026-07-02"),

    # Incident 13 [NOISE - COURT SENTENCING] - Date: 2026-07-02 (Same day as Borno Ambush)
    ("Legal risks and prolonged terror trials continue to strain federal judiciary budgets", "2026-07-02"),
    ("Court sentences notorious Boko Haram commander to life imprisonment", "2026-07-02"),
    ("Justice at last: Terror kingpin who masterminded 2022 church bombings bagged life jail", "2026-07-02"),
    ("War on terror: Federal High Court convicts top insurgent leader in Abuja", "2026-07-02"),
    ("Deconstructing the judicial bottlenecks in the prosecution of detained terror suspects", "2026-07-02"),
    ("Attorney-General hails landmark conviction of Boko Haram commander, promises speedy trials", "2026-07-02"),
    ("Breaking: Notorious terrorist commander sentenced to life imprisonment after 4-year trial", "2026-07-02"),
    ("Court jails dreaded bandit leader for life over multiple terror attacks", "2026-07-02"),
    ("Federal High Court sentences Boko Haram commander to life imprisonment", "2026-07-02"),
    ("INSIDE COURTROOM 4: How federal prosecutors secured life sentence for notorious terror mastermind", "2026-07-02"),

    # Incident 14 [VALID] - Date: 2026-07-04
    ("Foreign direct investment in solid minerals sector drops after Zamfara mining site assault", "2026-07-04"),
    ("Bandits storm Zamfara gold mine, kill four Chinese expatriates, abduct 9 locals", "2026-07-04"),
    ("Horrific invasion: Bandits gun down 4 Chinese engineers, drag 9 local miners into bush", "2026-07-04"),
    ("Zamfara gold rush crisis: Terrorists target foreign investors in deadly mining camp raid", "2026-07-04"),
    ("Solid mineral insecurity: The geopolitical fallout of targeted attacks on foreign workers in Zamfara", "2026-07-04"),
    ("Chinese Embassy issues security alert after 4 citizens are killed in Zamfara mining attack", "2026-07-04"),
    ("Zamfara mine bloodbath: How bandits outgunned security operatives, killed 4 Chinese, took 9 hostages", "2026-07-04"),
    ("4 Chinese nationals killed, 9 locals kidnapped in fresh Zamfara mine attack", "2026-07-04"),
    ("Four Chinese nationals killed, nine others abducted at Zamfara mining site", "2026-07-04"),
    ("Regulatory failure and illicit gold networks: The background to the Zamfara mine attack that killed 4 exportation workers", "2026-07-04"),

    # Incident 15 [VALID] - Date: 2026-07-05
    ("Institutional asset losses mount as police infrastructure targeted by South-East non-state actors", "2026-07-05"),
    ("Panic in Anambra as unknown gunmen attack police station, kill 3 officers, steal weapons", "2026-07-05"),
    ("Midday madness: Gunmen bomb Anambra police station, execute 3 cops, cart away rifles", "2026-07-05"),
    ("Subversive elements strike again: 3 police personnel killed in Anambra station raid", "2026-07-05"),
    ("De-escalating the sit-at-home enforcement violence: Analyzing the Anambra police station assault", "2026-07-05"),
    ("IGP orders immediate deployment of special tactical squads to Anambra after fatal station attack", "2026-07-05"),
    ("Anambra horror: Gunmen unleash fire on police station, set patrol vehicles ablaze, kill 3 cops", "2026-07-05"),
    ("3 policemen killed as unknown gunmen burn down station in Anambra", "2026-07-05"),
    ("Three police officers killed as gunmen attack divisional headquarters in Anambra", "2026-07-05"),
    ("How local vigilantes tried to repel the Anambra police station attack that left 3 officers dead", "2026-07-05"),

    # Incident 16 [NOISE - FOREIGN AID] - Date: 2026-07-05 (Same day as Anambra attack)
    ("US grants Nigeria $50m anti-terror funding, targets border drone surveillance tech", "2026-07-05"),
    ("US government donates $50m to Nigeria to combat terrorism, banditry", "2026-07-05"),
    ("Big boost: US gives Nigeria N75bn to wipe out Boko Haram, bandits", "2026-07-05"),
    ("Bilateral security alliance: Nigeria receives $50m counter-terrorism grant from United States", "2026-07-05"),
    ("Evaluating the impact of foreign military aid on Nigeria's internal security architecture", "2026-07-05"),
    ("US Ambassador clarifies conditions tied to the new $50m anti-terror package for Nigeria", "2026-07-05"),
    ("War on terror: US back Nigeria with $50m donation for tactical hardware", "2026-07-05"),
    ("Nigeria gets $50 million US grant to fight terrorism, pipeline vandalism", "2026-07-05"),
    ("US announces $50m grant to support Nigeria's counter-terrorism efforts", "2026-07-05"),
    ("ANALYSIS: Where will the new US $50 million anti-terror grant actually go?", "2026-07-05"),

    # Incident 17 [VALID] - Date: 2026-07-07
    ("Traditional institutional instability risks fracturing grassroots intelligence networks in the Northwest", "2026-07-07"),
    ("Shock in Katsina as bandits invade palace, abduct prominent traditional ruler", "2026-07-07"),
    ("Sacrilege in Katsina: Bandits overpower palace guards, kidnap First-Class Emir at midnight", "2026-07-07"),
    ("Katsina traditional stool desecrated: Bandits kidnap monarch, demand N500m ransom", "2026-07-07"),
    ("The vulnerability of traditional institutions: What the Katsina Emir's abduction tells us about rural security", "2026-07-07"),
    ("Northern Governors Forum condemns abduction of Katsina Emir, demands immediate military intervention", "2026-07-07"),
    ("Palace bloodletting: How bandits killed 2 guards to abduct 82-year-old Katsina traditional ruler", "2026-07-07"),
    ("Tension in Katsina as bandits kidnap prominent monarch from palace", "2026-07-07"),
    ("Bandits abduct traditional ruler from his palace in Katsina state", "2026-07-07"),
    ("Historical breakdown of traditional rulers targeted by bandits as Katsina Emir is kidnapped", "2026-07-07"),

    # Incident 18 [VALID] - Date: 2026-07-08
    ("Humanitarian crisis deepens as Benue IDP camp attacks threaten local farming labor pools", "2026-07-08"),
    ("Bloodbath in Benue: Armed herders invade IDP camp, kill 14 displaced persons", "2026-07-08"),
    ("No sanctuary: Gunmen slaughter 14 refugees, injure dozens in Benue IDP camp horror", "2026-07-08"),
    ("Middle Belt carnage: 14 refugees massacred in coordinated nighttime assault on Benue camp", "2026-07-08"),
    ("Secondary displacement and the failure of state protection in Benue's IDP camps", "2026-07-08"),
    ("Government officials call on UN to intervene as 14 are massacred in Benue displaced persons camp", "2026-07-08"),
    ("Benue massacre: Women, children hacked to death as invaders storm IDP camp at 1 am", "2026-07-08"),
    ("14 refugees killed, 25 injured in tragic Benue IDP camp attack", "2026-07-08"),
    ("14 killed, dozens injured in attack on Benue IDP camp", "2026-07-08"),
    ("Eyewitness accounts from the Benue IDP camp raid that left 14 dead", "2026-07-08"),

    # Incident 19 [NOISE - FAKE NEWS DEBUNK] - Date: 2026-07-08 (Same day as Benue attack)
    ("Misinformation on digital media risks causing artificial logistics panics across interstate trade routes", "2026-07-08"),
    ("Fake News: Army debunks viral video claiming terrorists took over Ekiti highway", "2026-07-08"),
    ("Don't panic! Video showing bandits operating on Ekiti road is fake, says military", "2026-07-08"),
    ("Cyber-terrorism or prank? Military dismisses trending clip of highway blockade in South-West", "2026-07-08"),
    ("The weaponization of digital anxiety: Understanding fake terror panics in southern Nigeria", "2026-07-08"),
    ("Defense Headquarters cautions citizens against spreading unverified videos of alleged terror attacks", "2026-07-08"),
    ("Ekiti road safe: Police, army expose source of viral fake video claiming bandit invasion", "2026-07-08"),
    ("Panic over alleged bandit takeover of Ekiti highway baseless — Police", "2026-07-08"),
    ("FACT CHECK: Viral video claiming bandits blocked major highway in Ekiti is old and misleading", "2026-07-08"),
    ("FACT CHECK: How a 4-year-old video from a foreign country was recycled as a 'terror attack' in Ekiti", "2026-07-08"),

    # Incident 20 [VALID] - Date: 2026-07-10
    ("Maritime insurance premiums spike as Niger Delta coastal piracy targets commercial passenger boats", "2026-07-10"),
    ("Tragedy on waterways: Sea pirates attack Rivers passenger boat, kill 3, abduct 8", "2026-07-10"),
    ("Terror on the high seas: Pirates ambush marine taxi, shoot 3 passengers dead, kidnap 8 traders", "2026-07-10"),
    ("Niger Delta security alert: 3 dead, 8 missing as sea pirates intensify coastal ambushes", "2026-07-10"),
    ("Resurgent maritime insecurity: Addressing the economic choking points of the Niger Delta creeks", "2026-07-10"),
    ("Navy deploys gunboats to Rivers creeks after pirates attack passenger boat, killing 3", "2026-07-10"),
    ("Creek bloodletting: How sea pirates intercepted Bonny-bound boat, killed 3, took 8 into mangrove forest", "2026-07-10"),
    ("3 killed, 8 kidnapped as sea pirates attack passenger boat in Rivers", "2026-07-10"),
    ("Three dead, eight abducted as sea pirates hijack passenger vessel in Rivers state", "2026-07-10"),
    ("Inside the deep mangrove camps where pirates are holding 8 abducted Rivers traders", "2026-07-10"),

    # Incident 21 [VALID] - Date: 2026-07-11
    ("Food inflation risks worsening as hidden IEDs force Yobe agrarian communities to abandon farmlands", "2026-07-11"),
    ("Tragic harvest: Landmine explosion kills six farmers in Yobe community", "2026-07-11"),
    ("Ripped apart: 6 local farmers killed by hidden Boko Haram IED inside Yobe farmland", "2026-07-11"),
    ("Insurgency residue: 6 rural farmers lose lives to improvised explosive device in Yobe", "2026-07-11"),
    ("Farmland contamination: The long-term threat of unexploded ordnances to North-East food security", "2026-07-11"),
    ("Yobe State Governor warns farmers against entering uncleared border forests after IED kills 6", "2026-07-11"),
    ("Yobe blast: 6 young farmers stepping on hidden landmine blown to pieces while harvesting crops", "2026-07-11"),
    ("6 farmers killed in tragic IED explosion in Yobe state", "2026-07-11"),
    ("Six farmers killed by improvised explosive device in Yobe", "2026-07-11"),
    ("Mapping the landmine threat: Why Yobe farms remain deadly years into the anti-terror war", "2026-07-11"),

    # Incident 22 [VALID] - Date: 2026-07-13
    ("Retail sector shocks: Weekly village markets hit hard by resurgence of urban suicide operations", "2026-07-13"),
    ("Suicide bombers strike crowded market, kill 18, injure 42", "2026-07-13"),
    ("Carnage at the market: Female suicide bomber detonates explosives among traders, killing 18", "2026-07-13"),
    ("Soft target strategy: 18 innocent shoppers killed in devastating market blast", "2026-07-13"),
    ("The psychology of crowd targets: Why market suicide bombings are returning to the fringes", "2026-07-13"),
    ("President expresses shock, orders immediate medical evacuation for 42 injured in market bombing", "2026-07-13"),
    ("Blood and scrap metal: 18 dismembered bodies recovered after market suicide blast", "2026-07-13"),
    ("18 killed, dozens rushed to hospital after horrific suicide bombing at local market", "2026-07-13"),
    ("18 dead, 42 injured in market suicide bomb attack", "2026-07-13"),
    ("Local security flaws that allowed suicide bomber to penetrate security perimeter at village market", "2026-07-13"),

    # Incident 23 [VALID] - Date: 2026-07-14
    ("Inter-communal land feuds in Plateau continue to devalue real estate and grazing rights investments", "2026-07-14"),
    ("Gunmen invade Plateau community, slaughter 11 residents in overnight attack", "2026-07-14"),
    ("Night of blood: Invaders slip past local guards, hack 11 to death in Plateau village", "2026-07-14"),
    ("Plateau cycle of violence: 11 lives lost as armed herdsmen launch reprisal raid", "2026-07-14"),
    ("Structural injustice and ethnic borders: Deconstructing the latest Plateau settlement massacre", "2026-07-14"),
    ("STF Commander moves tactical base after midnight attack leaves 11 dead in Plateau", "2026-07-14"),
    ("Plateau tears: How gunmen surrounded village, set 15 homes on fire, shot 11 fleeing residents", "2026-07-14"),
    ("11 killed, several houses razed in fresh Plateau midnight attack", "2026-07-14"),
    ("Gunmen kill 11 people, burn houses in fresh Plateau community assault", "2026-07-14"),
    ("Timeline of the fragile peace pacts that failed before the Plateau raid that claimed 11 lives", "2026-07-14")
]

df = pd.DataFrame(data_list, columns=['Headline', 'Date'])
df['Date'] = pd.to_datetime(df['Date'])

print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Encoding sentences...")
embeddings = model.encode(df['Headline'].tolist())

print("Computing custom distance matrix with strict 24-hour time constraint...")
base_distances = cosine_distances(embeddings)
n_samples = len(df)
custom_distances = np.zeros((n_samples, n_samples))

for i in range(n_samples):
    for j in range(n_samples):
        if i == j:
            custom_distances[i, j] = 0.0
            continue
            
        time_diff = abs((df.iloc[i]['Date'] - df.iloc[j]['Date']).total_seconds() / 3600) # hours
        
        # If the events occurred more than 24 hours apart, NEVER cluster them
        if time_diff > 24:
            custom_distances[i, j] = 2.0  # Max cosine distance
        else:
            custom_distances[i, j] = base_distances[i, j]

print("Clustering with Precomputed matrix...")
clustering_model = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=0.70, 
    metric='precomputed',
    linkage='average'
)
clustering_model.fit(custom_distances)

df['Cluster'] = clustering_model.labels_

# Output results
markdown_content = "# Hardcore Mock Clustering Test (Incidents 11-23)\n\n"
markdown_content += f"**Total Mock Articles:** {len(df)}\n"
markdown_content += f"**Total Clusters Identified:** {df['Cluster'].nunique()}\n\n---\n\n"

for cluster_id in sorted(df['Cluster'].unique()):
    markdown_content += f"### Incident Cluster {cluster_id}\n"
    cluster_docs = df[df['Cluster'] == cluster_id]
    for idx, row in cluster_docs.iterrows():
        # Tag specific noise indices based on the list positions
        # Incident 13 (indices 20-29), Incident 16 (indices 50-59), Incident 19 (indices 80-89)
        if (20 <= idx < 30) or (50 <= idx < 60) or (80 <= idx < 90):
             markdown_content += f"- **[{row['Date'].strftime('%Y-%m-%d')}]** 🚨 **TERROR NOISE:** {row['Headline']}\n"
        else:
             markdown_content += f"- **[{row['Date'].strftime('%Y-%m-%d')}]** {row['Headline']}\n"
    markdown_content += "\n"

with open("/home/seyi/.gemini/antigravity/brain/37d9ccba-8551-40a2-b1a9-038ecfdaa5eb/mock_experiment_results_tricky_noise.md", "w") as f:
    f.write(markdown_content)

print("Done!")
