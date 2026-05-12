# \# Xenos-Inspired Rasa Support Demo

# 

# This is a small Rasa Pro demo inspired by public observations of the Xenos Xenna chatbot experience.

# 

# The demo uses simulated Dutch customer-service queries only. It does not access real customer accounts, real orders, payment information, private Xenos systems, or personal data.

# 

# \## Purpose

# 

# The goal is to show how a Rasa-based assistant could improve common pre-handoff support journeys before routing a customer to a human medewerker.

# 

# The current observed pattern in the public Xenna flow is that a basic returns journey can be routed quickly toward staff. This demo explores how Rasa could make that journey more self-service capable while still escalating when human review is actually needed.

# 

# \## Demo scope

# 

# The assistant handles general support questions around:

# 

# \- returning an online order

# \- opened packaging

# \- damaged product received

# \- refund timing

# \- package marked as delivered but not received

# \- human handoff

# 

# \## Core demo conversation

# 

# 1\. `hoi`

# 2\. `Ik wil een online bestelling retourneren. Wat moet ik doen?`

# 3\. `Wat als de verpakking al geopend is?`

# 4\. `Het product is beschadigd aangekomen. Wat moet ik doen?`

# 5\. `Hoe lang duurt het voordat ik mijn geld terugkrijg?`

# 6\. `Mijn pakket staat op bezorgd, maar ik heb niets ontvangen. Wat moet ik doen?`

# 7\. `Kan ik hierover met een medewerker spreken?`

# 

# \## What the Rasa demo improves

# 

# | Observed Xenna pattern | Rasa demo improvement |

# |---|---|

# | Basic returns journey routed quickly to staff | Answers common return questions first |

# | Chatbot behaves mainly like a routing layer | Provides guided conversational support |

# | Human handoff happens early | Escalates only when order-specific review is needed |

# | Limited pre-handoff clarification | Handles follow-ups around packaging, damage, refund timing, and delivery |

# | Customer must wait for staff for common FAQ issues | Common questions are resolved immediately where possible |

# 

# \## Important limitation

# 

# This is not a production integration and does not claim to process real Xenos returns or check real orders.

# 

# The assistant only demonstrates how a Rasa-based support layer could guide users through common support scenarios and identify when a human medewerker is needed.

# 

# \## Environment

# 

# Tested with:

# 

# \- Python 3.11.9

# \- Rasa Pro 3.16.6

# \- Windows PowerShell

# 

# \## Run locally

# 

# Activate the virtual environment:

# 

# ```powershell

# .\\.venv\\Scripts\\Activate.ps1

