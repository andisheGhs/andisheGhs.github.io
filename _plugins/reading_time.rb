module Jekyll
  module ReadingTimeFilter
    def reading_time(input)
      words_per_minute = 200
      words = input.split.size
      reading_time = (words / words_per_minute).ceil
      reading_time = 1 if reading_time == 0
      reading_time
    end
  end
end

Liquid::Template.register_filter(Jekyll::ReadingTimeFilter)
