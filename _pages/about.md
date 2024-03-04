---
permalink: /
title: "About me"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

I am a PhD student in the Department of Computer Science at Northeastern University.


Education
======
* Ph.D in Computer Science, Northeastern University, 2024- (expected)
* M.S. in Computer Science, University of Paris, 2022-2023
* B.S. in Computer Science, Sharif University of Technology, 2017-2022

{% if site.author.googlescholar %}
  <div class="wordwrap">You can also find my articles on <a href="{{site.author.googlescholar}}">my Google Scholar profile</a>.</div>
{% endif %}

{% include base_path %}

{% for post in site.publications reversed %}
  {% include archive-single.html %}
{% endfor %}


