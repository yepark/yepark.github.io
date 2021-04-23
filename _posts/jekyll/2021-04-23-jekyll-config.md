#시간날때 마다 jekyll블로그에서 겪은 문제를 적어 놓겠음

1. 현재 jekyll minimal-mistakes 테마를 fork해서 사용중
2. 폰트 크기가 조정이 안되는 문제가 있음 https://github.com/mmistakes/minimal-mistakes/discussions/1219
3. disqus 설정 방법 site.comments.disqus.shortname 이거 해줘야함
4. disqus 설정시 웹페이지에 오류가 나는 경우
```html
{% if site.comments.disqus.shortname %}
<div id="disqus_thread"></div> // 이부분 추가
<script>
    /**
    *  RECOMMENDED CONFIGURATION VARIABLES: EDIT AND UNCOMMENT THE SECTION BELOW TO INSERT DYNAMIC VALUES FROM YOUR PLATFORM OR CMS.
    *  LEARN WHY DEFINING THESE VARIABLES IS IMPORTANT: https://disqus.com/admin/universalcode/#configuration-variables    */
    var disqus_config = function () {
      this.page.url = "{{ page.url | absolute_url }}";  /* Replace PAGE_URL with your page's canonical URL variable */
      this.page.identifier = "{{ page.id }}"; /* Replace PAGE_IDENTIFIER with your page's unique identifier variable */
    };
    (function() { // DON'T EDIT BELOW THIS LINE
    var d = document, s = d.createElement('script');
    s.src = 'https://{{ site.comments.disqus.shortname }}.disqus.com/embed.js';
    s.setAttribute('data-timestamp', +new Date());
    (d.head || d.body).appendChild(s);
    })();
</script>
<noscript>Please enable JavaScript to view the <a href="https://disqus.com/?ref_noscript">comments powered by Disqus.</a></noscript>
{% endif %}
```  

4. disqus광고 때문에 utterances로 갈아탐
_config.yml에 repository 설정 안해줘서 웹 에러남

일단 여기까지
