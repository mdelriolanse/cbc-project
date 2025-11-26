#!/usr/bin/env python3
"""
Script to populate the debate platform database with sample data.
Run this script to add sample topics and arguments for testing/demo purposes.
"""

import sys
import os

# Add backend directory to path so we can import database module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import database
from datetime import datetime

def populate_database():
    """Populate the database with sample topics and arguments."""
    
    print("Initializing database...")
    # Initialize database tables
    database.init_db()
    database.migrate_add_validity_columns()
    database.migrate_add_votes_column()
    database.ensure_argument_matches_table()
    
    print("Creating sample topics and arguments...")
    
    # Sample topic 1: Climate Change
    topic1 = database.create_topic(
        question="Should governments implement a carbon tax to combat climate change?",
        created_by="admin"
    )
    print(f"Created topic {topic1['id']}: Climate Change")
    
    # Pro arguments for topic 1
    arg1_pro1 = database.create_argument(
        topic_id=topic1['id'],
        side="pro",
        title="Economic Incentive for Clean Energy",
        content="A carbon tax creates a direct economic incentive for businesses and individuals to reduce their carbon emissions. By making fossil fuels more expensive, it encourages investment in renewable energy sources and energy-efficient technologies. Studies show that carbon pricing mechanisms have successfully reduced emissions in countries like Sweden and British Columbia.",
        author="EcoAdvocate",
        sources="https://www.worldbank.org/en/topic/climatechange/brief/carbon-pricing"
    )
    
    arg1_pro2 = database.create_argument(
        topic_id=topic1['id'],
        side="pro",
        title="Revenue for Green Infrastructure",
        content="Carbon tax revenue can be used to fund green infrastructure projects, subsidize renewable energy, and support communities affected by the transition. This creates a virtuous cycle where polluters pay for the solutions to the problems they create.",
        author="GreenPolicy",
        sources="https://www.cbo.gov/publication/58824"
    )
    
    # Con arguments for topic 1
    arg1_con1 = database.create_argument(
        topic_id=topic1['id'],
        side="con",
        title="Regressive Impact on Low-Income Households",
        content="Carbon taxes disproportionately affect low-income households who spend a larger percentage of their income on energy and transportation. Without proper rebates or offsets, carbon taxes can exacerbate economic inequality and create hardship for vulnerable populations.",
        author="EconomicJustice",
        sources="https://www.urban.org/research/publication/designing-carbon-tax-protect-low-income-households"
    )
    
    arg1_con2 = database.create_argument(
        topic_id=topic1['id'],
        side="con",
        title="Potential for Carbon Leakage",
        content="Implementing carbon taxes in isolation can lead to carbon leakage, where industries simply move to countries without carbon pricing. This doesn't reduce global emissions and can harm domestic industries and employment. A global approach is needed for effectiveness.",
        author="IndustryRep",
        sources="https://www.oecd.org/tax/tax-policy/carbon-leakage.htm"
    )
    
    # Add some votes
    database.upvote_argument(arg1_pro1)
    database.upvote_argument(arg1_pro1)
    database.upvote_argument(arg1_pro2)
    database.upvote_argument(arg1_con1)
    database.upvote_argument(arg1_con1)
    database.upvote_argument(arg1_con1)
    
    # Sample topic 2: Remote Work
    topic2 = database.create_topic(
        question="Is remote work more productive than in-office work?",
        created_by="admin"
    )
    print(f"Created topic {topic2['id']}: Remote Work")
    
    # Pro arguments for topic 2
    arg2_pro1 = database.create_argument(
        topic_id=topic2['id'],
        side="pro",
        title="Elimination of Commute Time",
        content="Remote work eliminates commute time, which can be 1-2 hours per day for many workers. This time savings directly translates to increased productivity, as employees can start work earlier, work longer, or use the time for rest and recovery. Studies show remote workers often work more hours than their in-office counterparts.",
        author="RemoteWorker",
        sources="https://www.gallup.com/workplace/283985/remote-work-rising-trend-continues.aspx"
    )
    
    arg2_pro2 = database.create_argument(
        topic_id=topic2['id'],
        side="pro",
        title="Fewer Distractions and Better Focus",
        content="Remote work environments typically have fewer interruptions from colleagues, impromptu meetings, and office noise. Many workers report being able to focus better at home, leading to deeper work and higher quality output. The ability to control one's environment is a significant productivity advantage.",
        author="ProductivityGuru",
        sources="https://www.microsoft.com/en-us/worklab/work-trend-index/productivity"
    )
    
    # Con arguments for topic 2
    arg2_con1 = database.create_argument(
        topic_id=topic2['id'],
        side="con",
        title="Reduced Collaboration and Innovation",
        content="In-person interactions foster spontaneous collaboration, creative problem-solving, and innovation. Remote work makes it harder to have impromptu conversations, read body language, and build the trust necessary for effective teamwork. Many breakthrough ideas come from casual office interactions.",
        author="TeamLeader",
        sources="https://hbr.org/2021/07/the-future-of-work-is-hybrid-heres-how-to-get-it-right"
    )
    
    arg2_con2 = database.create_argument(
        topic_id=topic2['id'],
        side="con",
        title="Difficulty Maintaining Work-Life Boundaries",
        content="Remote work can blur the lines between work and personal life, leading to burnout and decreased productivity over time. Without physical separation, workers may struggle to 'turn off' and may work longer hours without proper rest, ultimately reducing their effectiveness.",
        author="WorkLifeBalance",
        sources="https://www.mckinsey.com/featured-insights/future-of-work/americans-are-embracing-flexible-work-and-they-want-more-of-it"
    )
    
    # Add votes
    database.upvote_argument(arg2_pro1)
    database.upvote_argument(arg2_pro1)
    database.upvote_argument(arg2_pro2)
    database.upvote_argument(arg2_con2)
    
    # Sample topic 3: Universal Basic Income
    topic3 = database.create_topic(
        question="Should governments implement a Universal Basic Income (UBI)?",
        created_by="admin"
    )
    print(f"Created topic {topic3['id']}: Universal Basic Income")
    
    # Pro arguments for topic 3
    arg3_pro1 = database.create_argument(
        topic_id=topic3['id'],
        side="pro",
        title="Poverty Reduction and Economic Security",
        content="UBI provides a guaranteed income floor that eliminates extreme poverty and provides economic security for all citizens. It gives people the freedom to pursue education, start businesses, or take career risks without fear of destitution. Pilot programs in Finland and Canada showed positive effects on well-being and mental health.",
        author="SocialPolicy",
        sources="https://www.basicincome.org/research/"
    )
    
    # Con arguments for topic 3
    arg3_con1 = database.create_argument(
        topic_id=topic3['id'],
        side="con",
        title="Prohibitive Cost and Tax Burden",
        content="Implementing UBI at a meaningful level would require massive tax increases or cuts to other social programs. The cost could be trillions of dollars annually, potentially harming economic growth and creating unsustainable fiscal burdens. There are more cost-effective ways to address poverty.",
        author="FiscalConservative",
        sources="https://www.cbo.gov/publication/58824"
    )
    
    arg3_con2 = database.create_argument(
        topic_id=topic3['id'],
        side="con",
        title="Potential Reduction in Labor Force Participation",
        content="Some studies suggest that unconditional cash transfers may reduce labor force participation, particularly among low-wage workers. This could lead to labor shortages in essential industries and reduce overall economic productivity. The long-term economic impacts are uncertain.",
        author="LaborEconomist",
        sources="https://www.nber.org/papers/w22446"
    )
    
    # Add votes
    database.upvote_argument(arg3_pro1)
    database.upvote_argument(arg3_con1)
    database.upvote_argument(arg3_con1)
    database.upvote_argument(arg3_con2)
    
    # Sample topic 4: Social Media Regulation
    topic4 = database.create_topic(
        question="Should social media platforms be more heavily regulated by governments?",
        created_by="admin"
    )
    print(f"Created topic {topic4['id']}: Social Media Regulation")
    
    # Pro arguments for topic 4
    arg4_pro1 = database.create_argument(
        topic_id=topic4['id'],
        side="pro",
        title="Protection Against Misinformation and Harmful Content",
        content="Social media platforms have become vectors for misinformation, hate speech, and harmful content that can have real-world consequences. Government regulation can establish clear standards for content moderation, protect users from harmful algorithms, and hold platforms accountable for the content they amplify.",
        author="DigitalRights",
        sources="https://www.pewresearch.org/internet/2021/09/01/the-state-of-online-harassment/"
    )
    
    # Con arguments for topic 4
    arg4_con1 = database.create_argument(
        topic_id=topic4['id'],
        side="con",
        title="Threat to Free Speech and Innovation",
        content="Heavy government regulation of social media could lead to censorship and suppression of legitimate speech. Governments might use regulation as a tool to silence dissent or control information. Additionally, excessive regulation could stifle innovation and make it harder for new platforms to compete.",
        author="FreeSpeechAdvocate",
        sources="https://www.eff.org/issues/free-speech"
    )
    
    arg4_con2 = database.create_argument(
        topic_id=topic4['id'],
        side="con",
        title="Platforms Already Have Incentives to Self-Regulate",
        content="Social media platforms have strong business incentives to moderate content and protect users, as bad experiences drive users away. Many platforms have already implemented significant content moderation policies. Government regulation may be unnecessary and could create a one-size-fits-all approach that doesn't work for all platforms.",
        author="TechPolicy",
        sources="https://www.pewresearch.org/internet/2021/09/01/the-state-of-online-harassment/"
    )
    
    # Add votes
    database.upvote_argument(arg4_pro1)
    database.upvote_argument(arg4_pro1)
    database.upvote_argument(arg4_con1)
    
    print("\nDatabase population complete!")
    print(f"Created {4} topics with various arguments.")
    print("\nYou can now start the API server and view the populated data.")

if __name__ == "__main__":
    try:
        populate_database()
    except Exception as e:
        print(f"Error populating database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

