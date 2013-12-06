@use_splinter_client
Feature: Sign in

    # Scenario: Show signed in user name
    #    Given I am logged in as "Max" with email "test@example.com"
    #     when I go to "/_user"
    #     then I should get a "cache-control" header of "private, must-revalidate"
    #      and I should see the text "Signed in as Max"

    Scenario: Show signed in list of actions
       Given I am logged in as "Alex" with email "test@example.com"
         and I can upload to "my_bucket"
        when I go to "/_user"
        then I should see the text "Upload a CSV to the my_bucket bucket"
          and I should get a "x-frame-options" header of "SAMEORIGIN"
