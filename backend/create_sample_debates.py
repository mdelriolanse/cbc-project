#!/usr/bin/env python3
"""
Script to create three sample debates with varied argument quality.
Each debate has 2-3 pro and 2-3 con arguments.
Some arguments are well-researched, others are less so.
"""

import database
import fact_checker
import time

def create_sample_debates():
    """Create three sample debates with arguments of varying quality."""
    
    # Initialize database
    database.init_db()
    database.migrate_add_validity_columns()
    database.migrate_add_votes_column()
    
    debates = [
        {
            "question": "Should social media platforms be required to verify user identities?",
            "created_by": "admin",
            "pro_args": [
                {
                    "title": "Reduces online harassment and fake accounts",
                    "content": "Identity verification would significantly reduce anonymous trolling, cyberbullying, and the spread of misinformation. Studies show that platforms with verified users have 60% fewer harassment reports. Real-name policies in countries like South Korea have proven effective at curbing online abuse.",
                    "sources": "https://www.pewresearch.org/internet/2021/01/13/the-state-of-online-harassment/",
                    "quality": "high"
                },
                {
                    "title": "Prevents election interference",
                    "content": "Verified identities make it harder for foreign actors to create fake accounts and spread disinformation during elections. The 2016 and 2020 elections showed how unverified accounts can manipulate public discourse.",
                    "sources": "https://www.brookings.edu/articles/foreign-interference-in-elections/",
                    "quality": "high"
                },
                {
                    "title": "This is a bad idea",
                    "content": "you guys are wrong about this. social media is fine the way it is. stop trying to control everything",
                    "sources": "",
                    "quality": "low"
                }
            ],
            "con_args": [
                {
                    "title": "Privacy concerns and data security risks",
                    "content": "Requiring identity verification creates massive privacy risks. Centralized databases of user identities become targets for hackers. The 2017 Equifax breach exposed 147 million people's personal data. Social media platforms have poor security track records.",
                    "sources": "https://www.ftc.gov/news-events/news/press-releases/2019/07/equifax-pay-575-million-part-settlement-ftc-cfpb-states-regarding-2017-data-breach",
                    "quality": "high"
                },
                {
                    "title": "Disproportionately harms marginalized communities",
                    "content": "Identity verification requirements disproportionately impact LGBTQ+ individuals, activists, journalists, and people in authoritarian countries who need anonymity for safety. Real-name policies have been used to suppress dissent.",
                    "sources": "https://www.hrw.org/news/2021/03/15/china-social-media-platforms-should-protect-user-privacy",
                    "quality": "high"
                },
                {
                    "title": "Too expensive to implement",
                    "content": "this would cost way too much money. companies cant afford it",
                    "sources": "",
                    "quality": "low"
                }
            ]
        },
        {
            "question": "Should AI-generated content be required to have disclosure labels?",
            "created_by": "admin",
            "pro_args": [
                {
                    "title": "Prevents deception and maintains trust",
                    "content": "AI-generated content can be indistinguishable from human-created content, leading to deception. A 2023 study found that 85% of people cannot reliably identify AI-generated text. Disclosure labels are essential for maintaining trust in digital media.",
                    "sources": "https://www.nature.com/articles/s41598-023-43143-7",
                    "quality": "high"
                },
                {
                    "title": "Protects intellectual property and creative industries",
                    "content": "AI-generated content threatens jobs in creative industries. Without disclosure, AI content could flood markets and devalue human creativity. Labeling helps consumers make informed choices and supports human creators.",
                    "sources": "",
                    "quality": "medium"
                }
            ],
            "con_args": [
                {
                    "title": "Technically difficult to enforce",
                    "content": "Enforcing disclosure labels is nearly impossible. AI tools are widely available and constantly evolving. Bad actors will simply ignore labeling requirements. The technology to detect AI content is unreliable, with false positive rates as high as 30%.",
                    "sources": "https://arxiv.org/abs/2307.01908",
                    "quality": "high"
                },
                {
                    "title": "Stifles innovation and creative expression",
                    "content": "Mandatory labeling creates unnecessary barriers for legitimate uses of AI in creative work. Many artists use AI as a tool alongside traditional methods. Over-regulation could slow innovation in the creative technology sector.",
                    "sources": "",
                    "quality": "medium"
                },
                {
                    "title": "ai is bad",
                    "content": "i dont like ai. its going to take over the world. we should ban it completely",
                    "sources": "",
                    "quality": "low"
                }
            ]
        },
        {
            "question": "Should remote work be the default for knowledge workers?",
            "created_by": "admin",
            "pro_args": [
                {
                    "title": "Improves work-life balance and employee satisfaction",
                    "content": "Remote work significantly improves work-life balance. A 2022 survey of 10,000 knowledge workers found that 78% reported better work-life balance when working remotely. Employees save an average of 2.5 hours per day on commuting, which can be used for family time or personal development.",
                    "sources": "https://www.mckinsey.com/industries/real-estate/our-insights/americans-are-embracing-flexible-work-and-they-want-more-of-it",
                    "quality": "high"
                },
                {
                    "title": "Reduces carbon emissions and office costs",
                    "content": "Remote work reduces commuting, which accounts for 28% of greenhouse gas emissions in the US. Companies can also reduce office space costs by 30-50%. A study by Global Workplace Analytics estimated that remote work could reduce carbon emissions by 54 million tons annually.",
                    "sources": "https://www.globalworkplaceanalytics.com/telecommuting-statistics",
                    "quality": "high"
                },
                {
                    "title": "remote work is better",
                    "content": "working from home is just better. i can wear pajamas and no one cares",
                    "sources": "",
                    "quality": "low"
                }
            ],
            "con_args": [
                {
                    "title": "Hurts collaboration and team culture",
                    "content": "Remote work reduces spontaneous collaboration and weakens team bonds. Research from Microsoft found that remote work leads to fewer 'weak ties' - the casual connections that drive innovation. In-person interactions are crucial for building trust and company culture.",
                    "sources": "https://www.microsoft.com/en-us/worklab/work-trend-index/hybrid-work-is-just-work",
                    "quality": "high"
                },
                {
                    "title": "Creates inequality and isolation",
                    "content": "Remote work benefits those with dedicated home offices and stable internet, widening the gap between privileged and less-privileged workers. Many employees report increased feelings of isolation and loneliness when working fully remotely.",
                    "sources": "",
                    "quality": "medium"
                }
            ]
        }
    ]
    
    print("Creating sample debates...")
    
    for debate in debates:
        # Create topic
        topic_id = database.create_topic(
            question=debate["question"],
            created_by=debate["created_by"]
        )
        print(f"\n✓ Created topic: {debate['question']}")
        
        # Create pro arguments
        for arg in debate["pro_args"]:
            arg_id = database.create_argument(
                topic_id=topic_id,
                side="pro",
                title=arg["title"],
                content=arg["content"],
                author="sample_user",
                sources=arg.get("sources")
            )
            
            # Run fact-checking (this will assign validity scores)
            try:
                topic = database.get_topic(topic_id)
                verdict = fact_checker.verify_argument(
                    title=arg["title"],
                    content=arg["content"],
                    debate_question=topic["question"]
                )
                
                # Only save if relevant
                if verdict.is_relevant:
                    database.update_argument_validity(
                        argument_id=arg_id,
                        validity_score=verdict.validity_score,
                        validity_reasoning=verdict.reasoning,
                        key_urls=verdict.key_urls
                    )
                    print(f"  ✓ Pro: '{arg['title']}' - {verdict.validity_score}/5 stars")
                else:
                    print(f"  ✗ Pro: '{arg['title']}' - REJECTED (not relevant)")
            except Exception as e:
                print(f"  ⚠ Pro: '{arg['title']}' - Error during verification: {str(e)}")
            
            time.sleep(1)  # Rate limiting
        
        # Create con arguments
        for arg in debate["con_args"]:
            arg_id = database.create_argument(
                topic_id=topic_id,
                side="con",
                title=arg["title"],
                content=arg["content"],
                author="sample_user",
                sources=arg.get("sources")
            )
            
            # Run fact-checking
            try:
                topic = database.get_topic(topic_id)
                verdict = fact_checker.verify_argument(
                    title=arg["title"],
                    content=arg["content"],
                    debate_question=topic["question"]
                )
                
                # Only save if relevant
                if verdict.is_relevant:
                    database.update_argument_validity(
                        argument_id=arg_id,
                        validity_score=verdict.validity_score,
                        validity_reasoning=verdict.reasoning,
                        key_urls=verdict.key_urls
                    )
                    print(f"  ✓ Con: '{arg['title']}' - {verdict.validity_score}/5 stars")
                else:
                    print(f"  ✗ Con: '{arg['title']}' - REJECTED (not relevant)")
            except Exception as e:
                print(f"  ⚠ Con: '{arg['title']}' - Error during verification: {str(e)}")
            
            time.sleep(1)  # Rate limiting
    
    print("\n✅ Sample debates created successfully!")
    print("\nNote: Some arguments may be rejected if they contain no factual claims.")
    print("This is expected behavior - the fact-checker filters out irrelevant content.")

if __name__ == "__main__":
    create_sample_debates()

