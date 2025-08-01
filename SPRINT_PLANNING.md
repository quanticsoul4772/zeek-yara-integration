# Sprint Planning Guide

## Overview

This document provides detailed guidance for conducting effective sprint planning sessions for the Zeek YARA Integration project. Our sprint planning is designed to accommodate open-source community development with flexible contributor availability and diverse skill levels.

## Sprint Planning Objectives

### Primary Goals
1. **Define Clear Sprint Goal**: Establish what the team aims to achieve in the upcoming sprint
2. **Select Appropriate Work**: Choose user stories that align with sprint goal and team capacity
3. **Educational Alignment**: Ensure sprint work contributes to learning objectives
4. **Capacity Planning**: Match work to available contributor time and skills
5. **Risk Mitigation**: Identify and plan for potential blockers

### Success Metrics
- Sprint goal is clear and measurable
- All selected work has defined acceptance criteria
- Team capacity matches commitment
- Dependencies are identified and planned
- Educational value is articulated for each story

## Pre-Planning Preparation

### Product Owner Responsibilities (48 hours before)
1. **Backlog Refinement**
   - Ensure top backlog items have clear acceptance criteria
   - Update story priorities based on roadmap
   - Identify educational value for each story
   - Break down large stories (>8 points) into smaller ones

2. **Stakeholder Input**
   - Gather feedback from community discussions
   - Review recent user requests and issues
   - Assess roadmap progress and adjustments needed

3. **Dependency Analysis**
   - Identify external dependencies
   - Coordinate with other teams/projects if needed
   - Plan for resource availability

### Scrum Master Responsibilities (24 hours before)
1. **Logistics Preparation**
   - Schedule meeting and send calendar invites
   - Prepare virtual meeting room/tools
   - Set up sprint board and planning tools
   - Prepare planning materials and templates

2. **Team Coordination**
   - Confirm attendee availability
   - Send pre-read materials
   - Gather capacity information from team members
   - Prepare facilitation materials

### Development Team Responsibilities (Before planning)
1. **Capacity Assessment**
   - Review personal availability for upcoming sprint
   - Consider planned vacation, other commitments
   - Assess current skill levels for proposed work
   - Identify learning goals and interests

2. **Preparation Review**
   - Review product backlog and priorities
   - Understand current sprint goal progress
   - Prepare questions about unclear requirements
   - Consider technical dependencies and blockers

## Sprint Planning Meeting Structure

### Meeting Logistics
- **Duration**: 2-4 hours (scaled by sprint length and complexity)
- **Frequency**: Every 2 weeks (or at start of each sprint)
- **Participants**: Product Owner, Scrum Master, Development Team, Key Stakeholders (optional)
- **Format**: Virtual with screen sharing, collaborative tools

### Agenda Timeline

#### Part 1: Sprint Goal and Context (30-45 minutes)

##### 1. Sprint Review Context (10 minutes)
- **Previous Sprint Recap**
  - What was accomplished
  - What wasn't completed and why
  - Key learnings and improvements
  - Community feedback received

- **Current State Assessment**
  - Project roadmap progress
  - Technical debt status
  - Community engagement metrics
  - Educational goal progress

##### 2. Sprint Goal Definition (20-35 minutes)
- **Vision Alignment**
  - Review project vision and current phase
  - Identify key stakeholder priorities
  - Consider community feedback and requests

- **Goal Formulation**
  - Define specific, measurable sprint objective
  - Ensure alignment with quarterly milestones
  - Validate educational value
  - Confirm feasibility with team

**Sprint Goal Template:**
```
"By the end of this sprint, we will [achieve specific outcome] 
so that [target users] can [realize specific benefit], 
while learning [educational objectives]."
```

#### Part 2: Backlog Selection and Estimation (60-90 minutes)

##### 1. Story Review and Selection (45-60 minutes)
- **Priority Assessment**
  - Review top backlog items
  - Assess alignment with sprint goal
  - Consider dependencies and prerequisites
  - Evaluate educational value

- **Story Breakdown**
  - Break large stories into smaller tasks
  - Identify technical and educational components
  - Define clear acceptance criteria
  - Assign difficulty levels (Beginner/Intermediate/Advanced)

##### 2. Estimation Session (15-30 minutes)
- **Planning Poker Process**
  - Present each story to the team
  - Discuss complexity, unknowns, dependencies
  - Estimate using story point scale (1, 2, 3, 5, 8)
  - Reach consensus on effort required

**Estimation Considerations:**
- Technical complexity
- Domain knowledge required
- Testing effort
- Documentation needs
- Educational material creation
- Review and integration time

#### Part 3: Capacity Planning and Commitment (45-60 minutes)

##### 1. Team Capacity Assessment (20-30 minutes)
- **Individual Capacity**
  - Available hours per team member
  - Skill level match to proposed work
  - Learning objectives and mentoring needs
  - Other commitments and availability

- **Team Velocity**
  - Historical velocity analysis
  - Capacity adjustments for team changes
  - Holiday and vacation planning
  - Buffer for unexpected work

##### 2. Work Assignment and Commitment (25-30 minutes)
- **Story Assignment**
  - Match stories to contributor skills and interests
  - Identify mentoring pairs for learning opportunities
  - Balance workload across team members
  - Consider cross-training opportunities

- **Final Commitment**
  - Confirm team commitment to selected work
  - Validate sprint goal achievability
  - Identify potential risks and mitigation
  - Plan first few days of sprint work

## Planning Tools and Techniques

### Digital Tools
- **Project Board**: GitHub Projects or similar kanban tool
- **Estimation**: Planning Poker online tools
- **Documentation**: Shared documents for notes and decisions
- **Communication**: Video conferencing with screen sharing

### Planning Artifacts

#### Sprint Backlog Template
```markdown
# Sprint [Number] Backlog

## Sprint Goal
[Clear, measurable objective for the sprint]

## Sprint Duration
Start: [Date]
End: [Date]
Sprint Review: [Date/Time]
Retrospective: [Date/Time]

## Selected Stories

### High Priority
| Story | Points | Assignee | Status | Notes |
|-------|--------|----------|--------|-------|
| [Story title] | [Points] | [Name] | To Do | [Dependencies/Notes] |

### Medium Priority
| Story | Points | Assignee | Status | Notes |
|-------|--------|----------|--------|-------|

## Team Capacity
| Team Member | Available Hours | Committed Points | Learning Goals |
|-------------|----------------|------------------|----------------|
| [Name] | [Hours] | [Points] | [Learning objectives] |

## Dependencies and Risks
- [Dependency/Risk 1]: [Mitigation plan]
- [Dependency/Risk 2]: [Mitigation plan]

## Educational Objectives
- [Learning goal 1]
- [Learning goal 2]
- [Knowledge sharing plan]
```

### Story Breakdown Template
```markdown
# User Story: [Title]

## Story Description
**As a** [user type]
**I want** [functionality]
**So that** [benefit]

## Educational Value
**Learning Objectives**: [What users will learn]
**Difficulty Level**: [Beginner/Intermediate/Advanced]
**Prerequisites**: [Required knowledge/setup]

## Acceptance Criteria
- [ ] [Specific, testable condition]
- [ ] [Documentation updated]
- [ ] [Tests written and passing]
- [ ] [Educational materials created/updated]

## Technical Tasks
- [ ] [Technical task 1]
- [ ] [Technical task 2]
- [ ] [Testing task]
- [ ] [Documentation task]

## Definition of Done Checklist
- [ ] Code written and reviewed
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Educational materials created
- [ ] Security review completed
- [ ] Demo ready for sprint review
```

## Special Planning Considerations

### Community-Driven Development

#### Volunteer Availability
- **Flexible Commitment**: Allow for varying availability
- **Skill Development**: Include learning objectives in planning
- **Mentorship Planning**: Pair experienced and new contributors
- **Async Coordination**: Plan for different time zones and schedules

#### Educational Focus
- **Learning Outcomes**: Define what participants will learn
- **Skill Progression**: Plan for contributor advancement
- **Knowledge Sharing**: Include time for tutorials and demos
- **Documentation**: Ensure learning materials are maintained

### Risk Management in Planning

#### Common Risks
1. **Contributor Unavailability**: Plan for backup assignees
2. **Technical Blockers**: Include discovery time for complex stories
3. **Scope Creep**: Maintain focus on sprint goal
4. **Dependency Delays**: Identify critical path and alternatives

#### Mitigation Strategies
- **Buffer Planning**: Include 10-20% capacity buffer
- **Skill Redundancy**: Ensure multiple people can work on critical areas
- **Clear Priorities**: Maintain ordered backlog for scope adjustments
- **Regular Check-ins**: Plan mid-sprint progress reviews

## Planning Best Practices

### Facilitation Guidelines

#### For Scrum Masters
1. **Keep Discussions Focused**: Guide team back to planning objectives
2. **Encourage Participation**: Ensure all voices are heard
3. **Manage Time**: Use timeboxes to maintain meeting flow
4. **Document Decisions**: Capture key decisions and rationale
5. **Foster Learning**: Encourage questions and knowledge sharing

#### For Product Owners
1. **Clear Requirements**: Provide detailed story descriptions
2. **Flexible Prioritization**: Be open to technical constraints
3. **Educational Alignment**: Emphasize learning value
4. **Stakeholder Representation**: Bring community voice to planning

#### For Development Team
1. **Honest Estimation**: Provide realistic effort estimates
2. **Ask Questions**: Clarify requirements and dependencies
3. **Share Knowledge**: Help others understand technical aspects
4. **Commit Responsibly**: Only commit to achievable work

### Anti-Patterns to Avoid

#### Planning Meeting
- **Over-commitment**: Taking on more work than capacity allows
- **Under-detailed Stories**: Starting sprint with unclear requirements
- **Ignored Dependencies**: Failing to plan for external blockers
- **Weak Sprint Goal**: Vague or unmeasurable objectives

#### Team Dynamics
- **Dominant Voices**: Allowing few people to drive all decisions
- **Silent Participants**: Not engaging all team members
- **Technical Focus Only**: Ignoring educational and community aspects
- **Rigid Thinking**: Not adapting to new information or constraints

## Post-Planning Activities

### Immediate Actions (Same Day)
1. **Update Project Board**: Move selected stories to sprint backlog
2. **Send Summary**: Share planning results with team and stakeholders
3. **Set Up Communication**: Create sprint-specific channels or threads
4. **Schedule Check-ins**: Plan daily standups and mid-sprint reviews

### Sprint Kickoff (Next 1-2 Days)
1. **Task Breakdown**: Break stories into specific development tasks
2. **Environment Setup**: Ensure all contributors have necessary access
3. **Pair Assignments**: Connect mentors with mentees
4. **First Sprint Tasks**: Begin highest priority work

### Monitoring and Adjustment
1. **Daily Progress**: Track story completion and impediments
2. **Scope Management**: Adjust scope if capacity changes
3. **Learning Support**: Provide additional mentoring as needed
4. **Stakeholder Updates**: Keep community informed of progress

## Continuous Improvement

### Planning Retrospective Topics
- **Estimation Accuracy**: How well did estimates match actual effort?
- **Goal Achievement**: Did we accomplish the sprint goal?
- **Planning Effectiveness**: Was the planning meeting productive?
- **Team Satisfaction**: Were contributors engaged and satisfied?

### Metrics for Planning Quality
- **Commitment Accuracy**: Percentage of committed work completed
- **Estimation Variance**: Difference between estimated and actual effort
- **Planning Meeting Efficiency**: Time spent vs. value delivered
- **Team Engagement**: Participation levels and satisfaction scores

### Adaptation Strategies
- **Process Refinement**: Regularly update planning process based on feedback
- **Tool Optimization**: Improve or change tools that aren't working
- **Skill Development**: Identify and address planning skill gaps
- **Community Integration**: Better incorporate community feedback

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Next Review**: [Quarterly]  
**Maintainer**: Project Scrum Master

## Related Documents
- [AGILE_WORKFLOW.md](./AGILE_WORKFLOW.md) - Complete agile process overview
- [PROJECT_MILESTONES.md](./PROJECT_MILESTONES.md) - Milestone tracking and metrics
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Contribution guidelines
- [PROJECT_PLAN.md](./PROJECT_PLAN.md) - Overall project roadmap